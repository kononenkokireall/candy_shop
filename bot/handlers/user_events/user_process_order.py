# Класс фильтра для обработки действий по заказам
import logging

from aiogram import types, Bot
from aiogram.filters import Filter
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем запросы ORM для работы с БД
from database.orm_querys_order.orm_query_create_order import (
    orm_get_user_carts,
    orm_add_order,
    orm_get_info_pages,
    orm_get_order_details
)

from handlers.user_events.user_main import user_private_router
from keyboards.inline_main import OrderCallbackData
from keyboards.inline_pay import get_payment_keyboard


class OrderCallbackFilter(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        # Проверяем, начинается ли callback_data с "order:"
        return callback.data.startswith("order:")


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
