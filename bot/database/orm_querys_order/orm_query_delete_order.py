# Удаление заказа
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order


async def orm_delete_order(session: AsyncSession, order_id: int):
    """
    Удаляет заказ из базы данных.
    """
    query = (delete(Order)
             .where(Order.id == order_id))
    await session.execute(query)
    await session.commit()
