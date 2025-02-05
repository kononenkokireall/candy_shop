from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Order


# Функция получение заказов пользователя
async def orm_get_user_orders(session: AsyncSession, user_id: int):
    """
    Возвращает список заказов пользователя.
    """
    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.items))
        .order_by(Order.created.desc())  # Сортируем заказы по дате создания (последние выше)
    )
    result = await session.execute(query)
    return result.unique().scalars().all()