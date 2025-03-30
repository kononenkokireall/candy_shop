import logging

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import exc, select


from cache.decorators import cached
from database.models import Order, OrderItem

logger = logging.getLogger(__name__)

ORDER_TTL = 900  # 15 минут

# Функция Получает полную информацию о заказе с детализацией товаров
@cached("order:{order_id}", ttl=ORDER_TTL)
async def orm_get_order_details(
        session: AsyncSession, order_id: int
) -> Optional[Order]:
    """
    Получает полную информацию о заказе с детализацией товаров

    Параметры:
        session: Асинхронная сессия БД
        order_id: Идентификатор заказа

    Возвращает:
        Optional[Order]: Объект заказа с пред_загруженными:
            - items (список товаров)
            - product (информация о товаре для каждой позиции)
        None если заказ не найден

    Исключения:
        SQLAlchemyError: При ошибках выполнения запроса
    """
    logger.info(f"Запрос деталей заказа {order_id}")

    try:
        # Используем deselection для оптимизации загрузки связанных данных
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).joinedload(
                    OrderItem.product
                )  # Для загрузки продукта
            )
            .execution_options(populate_existing=True)
        )

        result = await session.execute(query)
        order = result.scalars().unique().one_or_none()

        if order:
            logger.debug(
                f"Успешно получен заказ {order_id}"
                f" с {len(order.items)} позициями"
            )
        else:
            logger.warning(f"Заказ {order_id} не найден в базе данных")

        return order.to_dict() if order else None

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка БД при получении заказа {order_id}: {str(e)}")
        raise
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при обработке заказа {order_id}")
        raise RuntimeError("Ошибка получения данных") from e
