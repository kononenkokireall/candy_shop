import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Order, User, OrderItem

# Функция уведомления администратора
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