# Получение деталей конкретного заказа
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Order, OrderItem


async def orm_get_order_details(session: AsyncSession, order_id: int):
    """
    Возвращает данные заказа и связанные с ним товары.
    """
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items)
                 .joinedload(OrderItem.product))
    )
    result = await session.execute(query)
    return result.unique().scalar()