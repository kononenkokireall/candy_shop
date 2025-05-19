from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, exc
import logging


from database.models import Product, OrderItem

# Настраиваем логгер для данного модуля
logger = logging.getLogger(__name__)


# Функция Добавляет список товаров в указанный заказ
# с валидацией и обработкой ошибок.
async def orm_add_order_items(
        session: AsyncSession,
        order_id: int,
        items: List[Dict[str, int | float]]
) -> int:
    logger.info(f"Добавление {len(items)} товаров в заказ {order_id}")

    if not isinstance(items, list):
        logger.error("Items должен быть списком")
        raise ValueError("Items должен быть списком")

    if len(items) == 0:
        logger.warning("Попытка добавить пустой список товаров")
        return 0

    required_keys = {"product_id", "quantity", "price"}
    for idx, item in enumerate(items, 1):
        if not all(key in item for key in required_keys):
            logger.error(f"Элемент {idx}: отсутствуют обязательные ключи")
            raise ValueError(f"Элемент {idx}: отсутствуют обязательные ключи")
        try:
            quantity = int(item["quantity"])
            price = float(item["price"])
        except (ValueError, TypeError) as e:
            logger.error(f"Элемент {idx}: некорректные типы данных")
            raise ValueError(f"Элемент {idx}: некорректные типы данных") from e

        if quantity < 1:
            logger.error(f"Элемент {idx}: количество должно быть больше 0")
            raise ValueError(f"Элемент {idx}: некорректное количество")
        if price < 0:
            logger.error(f"Элемент {idx}: цена не может быть отрицательной")
            raise ValueError(f"Элемент {idx}: некорректная цена")

    product_ids = [item["product_id"] for item in items]
    try:
        result = await session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        )
        existing_ids = {row for row in result.scalars()}
    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка проверки товаров: {str(e)}")
        raise RuntimeError("Ошибка проверки товаров") from e

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Не найдены товары с ID: {missing_ids}")
        raise ValueError(f"Несуществующие товары: {missing_ids}")

    insert_data = [
        {
            "order_id": order_id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": item["price"],
        }
        for item in items
    ]

    try:
        await session.execute(insert(OrderItem), insert_data)
        await session.commit()
        logger.info(
            f"Успешно добавлено {len(items)} товаров в заказ {order_id}")
        # await CacheInvalidator.invalidate([f"order:{order_id}"])
        return len(items)

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка добавления товаров: {str(e)}")
        raise RuntimeError("Ошибка добавления товаров") from e
    except Exception as e:
        await session.rollback()
        logger.exception("Неожиданная ошибка при добавлении товаров")
        raise RuntimeError("Внутренняя ошибка сервера") from e
