import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Order, OrderItem

# Настраиваем логгер
logger = logging.getLogger(__name__)



async def orm_get_user_orders(session: AsyncSession, user_id: int):
    """
    Возвращает список заказов пользователя.
    """
    logger.info(f"Получение списка заказов для пользователя {user_id}")

    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.items))
        .order_by(Order.created.desc())  # Сортируем заказы по дате создания (последние выше)
    )
    result = await session.execute(query)
    orders = result.unique().scalars().all()

    logger.debug(f"Найдено {len(orders)} заказов для пользователя {user_id}")
    return orders