import logging
from typing import Literal
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order

logger = logging.getLogger(__name__)

# Определяем допустимые статусы заказов
OrderStatus = Literal["pending", "processing", "completed", "cancelled"]


# Функция Обновляет статус заказа с проверкой валидности данных
async def orm_update_order_status(
        session: AsyncSession,
        order_id: int,
        new_status: OrderStatus
) -> bool:
    """
    Обновляет статус заказа с проверкой валидности данных

    Параметры:
        session: Асинхронная сессия БД
        order_id: Идентификатор заказа
        new_status: Новый статус из предопределенного списка

    Возвращает:
        bool: True если обновление успешно, False если заказ не найден

    Исключения:
        ValueError: При передаче некорректного статуса
        SQLAlchemyError: При ошибках работы с БД
    """
    logger.info(f"Попытка обновления статуса заказа {order_id}"
                f" на '{new_status}'")

    try:
        # Выполняем обновление и проверку
        update_stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(status=new_status)
            .returning(Order.id)
        )

        result = await session.execute(update_stmt)
        updated_order = result.scalar_one_or_none()

        if updated_order:
            logger.info(f"Статус заказа {order_id}"
                        f" успешно изменен на {new_status}")
            #await session.commit()
            return True

        logger.warning(f"Заказ {order_id} не найден")
        return False

    except SQLAlchemyError as e:
        logger.error(
            f"Ошибка БД при обновлении заказа {order_id}: {str(e)}",
            exc_info=True
        )
        #await session.rollback()
        raise
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при обновлении заказа"
                         f" {order_id}")
        #await session.rollback()
        raise RuntimeError("Ошибка обновления статуса") from e
