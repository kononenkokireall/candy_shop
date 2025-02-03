import os
import logging
from aiogram.filters import Filter
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
from aiogram import types, Router, Bot
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing.plugin.plugin_base import logging

# Импортируем запросы ORM для работы с БД
from database.orm_query import (
    orm_add_to_cart,
    orm_add_user,
    orm_get_info_pages,
    orm_add_order,
    orm_get_user_carts,
    orm_get_order_details,
)

# Импортируем пользовательские фильтры и вспомогательные модули
from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from keyboards.inline import MenuCallBack, get_payment_keyboard, OrderCallbackData

# Загружаем переменные окружения (например, ADMIN_ID)
load_dotenv()

# Создаем маршрутизатор для работы с маршрутами пользователя
user_private_router = Router()

# Указываем, что маршруты этого маршрутизатора применимы только для личных чатов
user_private_router.message.filter(ChatTypeFilter(["private"]))

# Получаем ID и никнейм администратора из переменных окружения
ADMIN_ID = str(os.getenv("ADMIN_ID"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")


# Handler для обработки команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # Получаем контент главного меню из базы данных
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    # Посылаем пользователю фотографию с заданным описанием и клавиатурой
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


# Функция добавления товара в корзину
async def add_to_cart(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    user_local = callback.from_user  # Получаем информацию о пользователе
    # Добавляем пользователя в базу данных
    await orm_add_user(
        session,
        user_id=user_local.id,
        first_name=user_local.first_name,
        last_name=user_local.last_name,
        phone=None,
    )
    # Добавляем товар в корзину
    await orm_add_to_cart(session, user_id=user_local.id, product_id=callback_data.product_id)
    # Отправляем уведомление пользователю
    await callback.answer("Товар добавлен в корзину!")


# Класс фильтра для обработки действий по заказам
class OrderCallbackFilter(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        # Проверяем, начинается ли callback_data с "order:"
        return callback.data.startswith("order:")


# # Handler для обработки заказов с фильтром "OrderCallbackFilter"
# @user_private_router.callback_query(OrderCallbackFilter())
# async def handle_order(callback: CallbackQuery):
#     # Извлекаем действие из callback_data (например: "create", "confirm")
#     action = callback.data.split(":")[1]
#     if action == "confirm":
#         # Обрабатываем подтверждение заказа
#         await callback.answer("Заказ оформлен!")


# Handler для обработки действий на основе данных OrderCallbackData
@user_private_router.callback_query(OrderCallbackData.filter())
async def process_order(
        callback: types.CallbackQuery,
        session: AsyncSession,
        bot: Bot,
):
    user = callback.from_user  # Получаем объект пользователя
    try:
        # Получаем товары из корзины
        cart_items = await orm_get_user_carts(session, user.id)
        if not cart_items:
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            return

        # Расчет общей стоимости
        total = sum(item.product.price * item.quantity for item in cart_items)

        # Формируем items для заказа
        order_items = [
            {
                "product_id": item.product.id,
                "quantity": item.quantity,
                "price": float(item.product.price)
            } for item in cart_items
        ]

        # Создаем заказ в базе данных
        order = await orm_add_order(
            session=session,
            user_id=user.id,
            total_price=total,
            items=order_items,
            status="pending"  # Добавляем статус заказа
        )

        # Получаем баннер для страницы оформления
        order_banner = await orm_get_info_pages(session, page="order")
        admin_link = order_banner[0].admin_link if order_banner else "https://t.me/CBDS_support"

        # Уведомление пользователя
        await callback.message.answer(
            f"✅ Заказ #{order.id} оформлен!\n"
            f"Сумма: {total} PLN\n"
            f"Свяжитесь с менеджером: {admin_link}",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Формируем детализированное сообщение для администратора
        order_details = await orm_get_order_details(session, order.id)
        order_text = (
            f"🛒 Новый заказ #{order.id}\n"
            f"👤 Пользователь: @{user.username}\n"
            f"📱 ID: {user.id}\n"
            f"📞 Контакт: {user.phone or 'не указан'}\n"
            f"💵 Сумма: {total} PLN\n\n"
            "Состав заказа:\n"
        )

        for item in order_details.items:
            order_text += f"- {item.product.name} ({item.quantity} шт. × {item.price} PLN)\n"

        # Отправляем админу уведомление с кнопкой подтверждения
        await bot.send_message(
            chat_id="https://t.me/CBDS_support",
            text=order_text,
            parse_mode="Markdown",
            reply_markup=get_payment_keyboard(order_id=order.id)  # Передаем ID заказа
        )

    except Exception as e:
        logging.error(f"Ошибка при оформлении заказа: {str(e)}", exc_info=True)
        await callback.message.answer(
            "⚠️ Произошла ошибка при оформлении заказа. Попробуйте позже."
        )
    finally:
        await callback.answer()



# Handler для обработки пользовательского меню на основе данных MenuCallBack
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    if callback_data.menu_name == "add_to_cart":  # Если действие - добавление в корзину
        await add_to_cart(callback, callback_data, session)
        return

    # Получаем контент меню из базы данных
    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        user_id=callback.from_user.id,
        product_id=callback_data.product_id,
    )
    # Обновляем содержимое сообщения с новым медиа и клавиатурой
    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
