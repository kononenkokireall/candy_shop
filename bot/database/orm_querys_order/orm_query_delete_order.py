import logging
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order

# Настраиваем логгер
logger = logging.getLogger(__name__)


######################## Удаление заказа #######################################

async def orm_delete_order(session: AsyncSession, order_id: int):
    """
    Удаляет заказ из базы данных.
    """
    logger.info(f"Попытка удаления заказа {order_id}")

    query = delete(Order).where(Order.id == order_id)
    result = await session.execute(query)
    await session.commit()

    if result.rowcount() > 0:
        logger.info(f"Заказ {order_id} успешно удален")
    else:
        logger.warning(f"Заказ {order_id} не найден в базе")
