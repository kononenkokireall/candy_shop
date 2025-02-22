# ------------------------- Работа с заказами -------------------------
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Order, OrderItem


async def get_full_order(session: AsyncSession, order_id: int) -> str:
    """Получение полных данных заказа с отношениями"""
    stmt = await session.execute(
        select(Order)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .where(Order.id == order_id)
    )
    # Выполняем запрос
    result = await session.execute(stmt)
    order = result.scalars().first()