from aiogram import F, types
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, Cart
from handlers.admin_events.admin_main import admin_router

# Функция подтверждения заказа администратором
@admin_router.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[-1])

    # Очищаем корзину пользователя
    order = await session.get(Order, order_id)
    await session.execute(delete(Cart).where(Cart.user_id == order.user_id))

    # Обновляем статус заказа
    order.status = "completed"
    await session.commit()

    await callback.message.edit_text(
        f"✅ Заказ #{order_id} подтвержден и оплачен!",
        reply_markup=None
    )
    await callback.answer()