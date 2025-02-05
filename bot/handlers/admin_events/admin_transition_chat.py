from aiogram.types import InputMediaPhoto, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, OrderItem
from database.orm_querys_order.orm_query_create_order import orm_get_banner, orm_get_user_carts
from handlers.admin_events.admin_notify import notify_admin
from keyboards.inline_main import MenuCallBack
from main import bot #!


# Функция для завершения покупки и перехода в чат с администратором
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