import logging

from sqlalchemy import delete, exc
from sqlalchemy.ext.asyncio import AsyncSession

from cache.invalidator import CacheInvalidator
from database.models import OrderItem, Order

# Настраиваем логгер
logger = logging.getLogger(__name__)


# Функция Безопасно удаляет заказ и все связанные данные
async def orm_delete_order(
        session: AsyncSession,
        order_id: int
) -> bool:
    """
    Безопасно удаляет заказ и все связанные данные

    Параметры:
        session (AsyncSession): Асинхронная сессия БД
        order_id (int): Идентификатор заказа для удаления

    Возвращает:
        bool: True если удаление успешно, False если заказ не найден

    Исключения:
        SQLAlchemyError: При ошибках работы с базой данных
    """
    logger.info(f"Попытка удаления заказа {order_id}")

    try:
        async with session.begin():  # Использование транзакции
            # Удаление связанных элементов заказа
            await session.execute(
                delete(OrderItem).where(OrderItem.order_id == order_id)
            )

            # Удаление основного заказа
            deleted_id = await session.scalar(
                delete(Order).where(Order.id == order_id).returning(Order.id)
            )

            if deleted_id:
                # Инвалидация кэша заказа и списка заказов
                await CacheInvalidator.invalidate([
                    f"order:{order_id}"
                ])
                logger.info(f"Заказ {order_id} успешно удален")
                return True

            logger.warning(f"Заказ {order_id} не найден")
            return False

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка удаления заказа {order_id}: {str(e)}")
        await session.rollback()
        raise
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при удалении заказа {order_id}")
        await session.rollback()
        raise RuntimeError("Ошибка удаления заказа") from e
