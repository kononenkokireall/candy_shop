from aiogram import types, Router
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from telegram import InputMediaPhoto

from database.models import Order, OrderItem, User, Cart
from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_cart import orm_add_to_cart
from database.orm_querys.orm_query_user import orm_add_user

# Импортируем пользовательские фильтры и вспомогательные модули
from filters.chat_types import ChatTypeFilter
from handlers.admin_events.admin_main import checkout

from handlers.menu_events.menu_processing_get import get_menu_content
from keyboards.inline_main import MenuCallBack
from utilit.notification import NotificationService, get_notification_service

# Создаем маршрутизатор для работы с маршрутами пользователя
user_private_router = Router()

# Указываем, что маршруты этого маршрутизатора применимы только для личных чатов
user_private_router.message.filter(ChatTypeFilter(["private"]))


##############################Handler команды /start для пользователя##################################################

# Handler для обработки команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # Получаем контент главного меню из базы данных
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    # Посылаем пользователю фотографию с заданным описанием и клавиатурой
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


#########################Handler обработки добавления товара в корзину для пользователя################################

# Функция добавления товара в корзину
# Функция добавления товара в корзину
async def add_to_cart(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession
):
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

##################################Handler обработки меню для пользователя##############################################

# Handler для обработки пользовательского меню на основе данных MenuCallBack
@user_private_router.callback_query(MenuCallBack.filter())
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
        notification_service: NotificationService = None
):
    if notification_service is None:
        notification_service = get_notification_service()

    if callback_data.menu_name == "checkout" and callback_data.level == 4:
        media, keyboards = await checkout(session, callback.from_user.id, notification_service)
        await callback.message.edit_media(media=media, reply_markup=keyboards)
        await callback.answer()


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

    # Проверяем, что media и reply_markup корректны
    if not media:
        await callback.answer("Медиа не найдено.", show_alert=True)
        return

    # Если media — это строка, оборачиваем её в InputMediaPhoto
    if isinstance(media, str):
        media = InputMediaPhoto(media=media)

    # Лог данные для отладки
    print("Media:", media)
    print("Reply Markup:", reply_markup)

    # Обновляем содержимое сообщения с новым медиа и клавиатурой
    try:
        await callback.message.edit_media(media=media, reply_markup=reply_markup)
    except Exception as e:
        print("Ошибка при изменении медиа:", e)
        await callback.answer("Произошла ошибка при обновлении медиа.", show_alert=True)

    await callback.answer()

##############################Handler текста с деталями заказа для пользователя########################################
#
# # Функция генерации текста с деталями заказа
# async def generate_order_summary(order_id: int, session: AsyncSession) -> str:
#     """Генерирует текст с деталями заказа"""
#     order = await session.get(Order, order_id)
#     items = await session.execute(
#         select(OrderItem)
#         .where(OrderItem.order_id == order_id)
#         .options(joined_load(OrderItem.product))
#     )
#     items = items.scalars().all()
#
#     payment_info = await orm_get_banner(session, "payment_info")
#
#     summary = (
#         "📝 *Детали вашего заказа:*\n\n"
#         "🛒 *Состав заказа:*\n"
#     )
#
#     for item in items:
#         summary += f"• {item.product.name} - {item.quantity} шт. × {item.product.price} PLN\n"
#
#     summary += (
#         f"\n💵 *Итого к оплате:* {order.total_price} PLN\n\n"
#         f"💳 *Способы оплаты:*\n{payment_info.description}\n\n"
#         "📦 *Условия доставки:*\n"
#         "Доставка осуществляется в течение 2-3 рабочих дней. "
#         "Самовывоз доступен из нашего офиса по адресу: ..."
#     )
#
#     return summary
