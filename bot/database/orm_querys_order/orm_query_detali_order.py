import logging
# Получение деталей конкретного заказа
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Order, OrderItem

logger = logging.getLogger(__name__)

async def orm_get_order_details(session: AsyncSession, order_id: int):
    """
    Возвращает данные заказа и связанные с ним товары.
    """
    logger.info(f"Получение деталей заказа {order_id}")

    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )
    result = await session.execute(query)
    order = result.unique().scalar()

    if order:
        logger.debug(f"Детали заказа {order_id} получены успешно")
    else:
        logger.warning(f"Заказ {order_id} не найден")

    return order