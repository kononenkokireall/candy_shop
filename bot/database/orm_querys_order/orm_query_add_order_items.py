from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, exc
import logging
from database.models import Product, OrderItem

logger = logging.getLogger(__name__)

async def orm_add_order_items(
    session: AsyncSession,
    order_id: int,
    items: List[Dict]
) -> int:
    """
    Добавляет список товаров в указанный заказ с валидацией и обработкой ошибок

    Параметры:
        session (AsyncSession): Асинхронная сессия БД
        order_id (int): Идентификатор заказа
        items (List[Dict]): Список словарей с товарами вида:
            {
                "product_id": int,
                "quantity": int (>0),
                "price": float (>=0)
            }

    Возвращает:
        int: Количество добавленных товаров

    Исключения:
        ValueError: При некорректных входных данных
        RuntimeError: При ошибках работы с БД
    """
    logger.info(f"Добавление {len(items)} товаров в заказ {order_id}")

    # Валидация входных данных
    if not isinstance(items, list):
        logger.error("Items должен быть списком")
        raise ValueError("Items должен быть списком")

    if len(items) == 0:
        logger.warning("Попытка добавить пустой список товаров")
        return 0

    # Подробная проверка каждого элемента
    required_keys = {"product_id", "quantity", "price"}
    for idx, item in enumerate(items, 1):
        if not all(key in item for key in required_keys):
            logger.error(f"Элемент {idx}: отсутствуют обязательные ключи")
            raise ValueError(f"Элемент {idx}: отсутствуют обязательные ключи")

        try:
            product_id = int(item["product_id"])
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

    # Проверка существования товаров
    product_ids = [item["product_id"] for item in items]
    try:
        result = await session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        )
        existing_ids = {row.id for row in result.scalars()}
    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка проверки товаров: {str(e)}")
        raise RuntimeError("Ошибка проверки товаров") from e

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Не найдены товары с ID: {missing_ids}")
        raise ValueError(f"Несуществующие товары: {missing_ids}")

    # Формирование данных для вставки
    insert_data = [
        {
            "order_id": order_id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": item["price"]
        }
        for item in items
    ]

    # Массовая вставка с обработкой транзакции
    try:
        async with session.begin():
            await session.execute(
                insert(OrderItem),
                insert_data
            )
        logger.info(f"Успешно добавлено {len(items)} товаров в заказ {order_id}")
        return len(items)

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка добавления товаров: {str(e)}")
        raise RuntimeError("Ошибка добавления товаров") from e
    except Exception as e:
        logger.exception("Неожиданная ошибка при добавлении товаров")
        raise RuntimeError("Внутренняя ошибка сервера") from e