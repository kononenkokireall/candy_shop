import logging
from sqlalchemy import  update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order

# Настраиваем логгер
logger = logging.getLogger(__name__)


async def orm_update_order_status(session: AsyncSession, order_id: int, new_status: str):
    """
    Изменяет статус заказа.
    """
    logger.info(f"Обновление статуса заказа {order_id} на '{new_status}'")

    query = update(Order).where(Order.id == order_id).values(status=new_status)
    result = await session.execute(query)
    await session.commit()

    if result.rowcount() > 0:
        logger.info(f"Статус заказа {order_id} успешно обновлен на '{new_status}'")
    else:
        logger.warning(f"Заказ {order_id} не найден или статус не изменен")