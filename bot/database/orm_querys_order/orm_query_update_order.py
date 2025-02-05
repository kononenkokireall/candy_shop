# Обновление статуса заказа
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order


async def orm_update_order_status(
        session: AsyncSession,
        order_id: int,
        new_status: str
):
    """
    Изменяет статус заказа.
    """
    query = (
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await session.execute(query)
    await session.commit()