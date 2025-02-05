from aiogram import F, types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_delete_product
from handlers.admin_events.admin_main import admin_router


# Handler для удаления товара
@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1] # Получаем ID продукта для удаления
    await orm_delete_product(session, int(product_id)) # Удаляем товар из базы данных

    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")