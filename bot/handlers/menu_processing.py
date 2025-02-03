import logging
import os

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto, InlineKeyboardButton
from sqlalchemy.orm import joinedload

from database.models import Order, OrderItem, User
# Импортируем запросы ORM для работы с базой данных
from database.orm_query import (
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_delete_from_cart,
    orm_reduce_product_in_cart,
    orm_add_to_cart,
    orm_get_user_carts
)

# Импортируем модули для создания клавиатуры
from keyboards.inline import (
    get_user_main_btn,
    get_user_catalog_btn,
    get_user_product_btn,
    get_user_cart_btn,
    MenuCallBack
)

from utilit.paginator import Paginator


bot = Bot(token=os.getenv('TOKEN'))

# Функция для формирования главного меню (уровень 0)
async def main_menu(session, level, menu_name):
    # Получаем баннер из базы данных для заданного меню
    banner = await orm_get_banner(session, menu_name)
    # Подготавливаем изображение для отправки пользователю
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    # Генерируем клавиатуру для главного меню
    keyboards = get_user_main_btn(level=level)
    return image, keyboards


# Функция для формирования меню каталога (уровень 1)
async def catalog(session, level, menu_name):
    # Получаем баннер для каталога
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    # Загружаем список категорий из базы данных
    categories = await orm_get_categories(session)
    # Генерируем клавиатуру для категорий
    keyboards = get_user_catalog_btn(level=level, categories=categories)
    return image, keyboards


# Функция для создания кнопок постраничной навигации
def pages(paginator: Paginator):
    btn = dict()
    # Если доступна предыдущая страница, добавляем кнопку "Пред."
    if paginator.has_previous():
        btn["◀️Пред."] = "prev"
    # Если доступна следующая страница, добавляем кнопку "След."
    if paginator.has_next():
        btn["След.▶️"] = "next"
    return btn


# Функция для отображения товаров из каталога (уровень 2)
async def products(session, level, category, page):
    # Получаем список товаров из категории
    products_user = await orm_get_products(session, category_id=category)
    paginator = Paginator(products_user, page=page)
    product_user = paginator.get_page()[0]  # Берем первый товар на текущей странице
    # Создаем медиа-объект для продукта
    image = InputMediaPhoto(
        media=product_user.image,
        caption=f"<strong>{product_user.name}</strong>\n{product_user.description}\n"
                f"Стоимость: {round(product_user.price, 2)} PLN.\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    # Создаем кнопки навигации для пагинации
    pagination_btn = pages(paginator)
    keyboards = get_user_product_btn(
        level=level,
        category=category,
        page=page,
        pagination_btn=pagination_btn,
        product_id=product_user.id,
    )

    return image, keyboards


# Функция для управления корзиной (уровень 3)
async def carts(session, level, menu_name, page, user_id, product_id):
    # Обработка действий в корзине
    if menu_name == 'delete':  # Удаление товара из корзины
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1: page -= 1  # Проверяем текущую страницу
    elif menu_name == 'decrement':  # Уменьшение количества товара
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart: page -= 1
    elif menu_name == 'increment':  # Увеличение количества товара
        await orm_add_to_cart(session, user_id, product_id)

    # Получаем содержимое корзины пользователя
    carts_user = await orm_get_user_carts(session, user_id)

    if not carts_user:  # Если корзина пуста, показываем баннер
        banner = await orm_get_banner(session, 'cart')
        image = InputMediaPhoto(media=banner.image, caption=f"<strong>{banner.description}</strong>")
        keyboards = get_user_cart_btn(
            level=level,
            page=None,
            pagination_btn=None,
            product_id=None,
        )
    else:
        # Если в корзине есть товары, используем paginator
        paginator = Paginator(carts_user, page=page)
        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(sum(cart.quantity * cart.product.price for cart in carts_user), 2)
        # Отображаем информацию о текущем товаре из корзины и общую сумму
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n"
                    f"{cart.product.price}.PLN x {cart.quantity} = {cart_price}.PLN\n"
                    f"Товар {paginator.page} из {paginator.pages} в корзине.\n"
                    f"Общая сумма товаров в корзине: {total_price}.PLN",
        )

        # Генерируем кнопки для управления корзиной (навигатор)
        pagination_btn = pages(paginator)
        keyboards = get_user_cart_btn(
            level=level,
            page=page,
            pagination_btn=pagination_btn,
            product_id=cart.product.id,
        )
    return image, keyboards


async def notify_admin(order_id: int, session: AsyncSession, bot: Bot):
    try:
        # 1. Получаем заказ с проверкой на существование
        order = await session.get(Order, order_id)
        if not order:
            logging.error(f"Заказ #{order_id} не найден")
            return

        # 2. Получаем пользователя через user_id (BigInteger)
        user = await session.execute(
            select(User)
            .where(User.user_id == order.user_id)  # Используем user_id вместо id
            .limit(1)
        )
        user = user.scalar()

        if not user:
            logging.error(f"Пользователь для заказа #{order_id} не найден")
            return

        # 3. Получаем состав заказа
        order_items = await session.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .options(joinedload(OrderItem.product))
        )
        items = order_items.scalars().all()

        # 4. Формируем сообщение
        if user.first_name:
            user_line = f"[{user.first_name}](tg://user?id={user.user_id})"
        else:
            user_line = "не указано"

        message = (
            f"🛒 **Новый заказ #{order_id}**\n"
            f"👤 Пользователь: {user_line}\n"
            f"📱 ID: {user.user_id}\n"
            f"📞 Контакт: {user.phone or 'не указан'}\n"
            f"📦 Статус: {order.status}\n\n"
            "**Состав заказа:**\n"
        )

        for item in items:
            if item.product:  # Проверка на существование товара
                message += f"- {item.product.name} ({item.quantity} × {item.price} PLN)\n"
            else:
                message += f"- Товар удалён (ID: {item.product_id})\n"

        message += f"\n💵 **Итого:** {order.total_price} PLN"

        # 5. Создаем клавиатуру
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text="✅ Подтвердить заказ",
                callback_data=f"confirm_order_{order_id}"
            )
        )

        # 6. Отправляем сообщение (исправлен chat_id)
        await bot.send_message(
            chat_id='7552593310'
,  # Используйте числовой ID чата
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logging.error(f"Ошибка уведомления админа: {str(e)}", exc_info=True)
        # Можно добавить повторную попытку или уведомление разработчикам


async def checkout(session: AsyncSession, user_id: int):
    """Функция для завершения покупки и перехода в чат с администратором"""
    # Получаем баннер с информацией о чате администратора
    banner = await orm_get_banner(session, 'order')

    # Получаем содержимое корзины пользователя
    carts_user = await orm_get_user_carts(session, user_id)
    total_price = sum(item.quantity * item.product.price for item in carts_user)

    # Создаем заказ
    order = Order(user_id=user_id, total_price=total_price, status="pending")
    session.add(order)
    await session.flush()  # Получаем ID заказа

    # Добавляем товары в заказ
    for cart_item in carts_user:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        session.add(order_item)
        await session.commit()

        # Отправляем уведомление администратору
        await notify_admin(order.id, session, bot)


    # Формируем сообщение с благодарностью
    caption = (f"🎉 Спасибо за покупку! 🎉\n\n"
               f"Общая сумма заказа: {total_price} PLN\n"
               f"Для завершения оформления перейдите в чат с менеджером: {banner.admin_link}")

    image = InputMediaPhoto(media=banner.image, caption=caption)

    # Создаем клавиатуру с кнопкой для перехода в чат
    keyboards = InlineKeyboardBuilder()
    keyboards.add(InlineKeyboardButton(
            text="Обратно в меню",
            callback_data=MenuCallBack(level=0, menu_name='main').pack()
    ))

    return image, keyboards.as_markup()


# Функция для обработки запросов меню на основе уровня и действия
async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        product_id: int | None = None,
        category: int | None = None,
        page: int | None = None,
        user_id: int | None = None,
):
    # Проверяем уровень меню и вызываем соответствующую функцию
    if level == 0:  # Главная страница
        return await main_menu(session, level, menu_name)
    elif level == 1:  # Каталог
        return await catalog(session, level, menu_name)
    elif level == 2:  # Товары в каталоге
        return await products(session, level, category, page)
    elif level == 3:  # Корзина
        return await carts(session, level, menu_name, page, user_id, product_id)
    elif level == 4:  # Новый уровень для завершения покупки
        return await checkout(session,  user_id)
