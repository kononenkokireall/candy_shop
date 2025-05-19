import logging

from sqlalchemy import delete, exc
from sqlalchemy.ext.asyncio import AsyncSession

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
        ValueError: При некорректном order_id
        SQLAlchemyError: При ошибках работы с базой данных
    """
    logger.info(f"Попытка удаления заказа {order_id}")

    try:
        # Валидация идентификатора заказа
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(
                "Некорректный идентификатор заказа: "
                "должен быть положительным целым числом"
            )

        # Удаление связанных элементов заказа
        await session.execute(
            delete(OrderItem).where(OrderItem.order_id == order_id)
        )

        # Удаление основного заказа
        deleted_id = await session.scalar(
            delete(Order).where(Order.id == order_id).returning(Order.id)
        )

        if deleted_id:
            await session.commit()
            logger.info(f"Заказ {order_id} успешно удален")
            return True

        logger.warning(f"Заказ {order_id} не найден")
        return False

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка удаления заказа {order_id}: {str(e)}",
                     exc_info=True)
        raise
    except ValueError as e:  # Теперь перехватывает ошибки валидации
        logger.warning(f"Некорректные параметры запроса: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.exception(f"Неожиданная ошибка при удалении заказа {order_id}")
        raise RuntimeError("Ошибка удаления заказа") from e
