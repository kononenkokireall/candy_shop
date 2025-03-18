from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, exc
import logging
from database.models import Product, OrderItem

# Настраиваем логгер для данного модуля
logger = logging.getLogger(__name__)


async def orm_add_order_items(
        session: AsyncSession,
        order_id: int,
        items: List[Dict[str, int | float]]
) -> int:
    """
    Добавляет список товаров в указанный заказ
     с валидацией и обработкой ошибок.

    Параметры:
      - session (AsyncSession): Асинхронная сессия БД.
      - order_id (int): Идентификатор заказа.
      - items (List[Dict]): Список словарей с товарами вида:
            {
                "product_id": int,
                "quantity": int (>0),
                "price": float (>=0)
            }

    Возвращает:
      - int: Количество добавленных товаров.

    Исключения:
      - ValueError: При некорректных входных данных.
      - RuntimeError: При ошибках работы с БД.
    """
    logger.info(f"Добавление {len(items)} товаров в заказ {order_id}")

    # Валидация входных данных: items должен быть списком
    if not isinstance(items, list):
        logger.error("Items должен быть списком")
        raise ValueError("Items должен быть списком")

    # Если список пуст, логируем предупреждение и возвращаем 0
    if len(items) == 0:
        logger.warning("Попытка добавить пустой список товаров")
        return 0

    # Определяем обязательные ключи,
    # которые должны присутствовать в каждом элементе списка
    required_keys = {"product_id", "quantity", "price"}
    # Проверка каждого элемента списка
    # на наличие обязательных ключей и корректность значений
    for idx, item in enumerate(items, 1):
        # Если хотя бы один обязательный ключ отсутствует,
        # логируем ошибку и выбрасываем исключение
        if not all(key in item for key in required_keys):
            logger.error(f"Элемент {idx}: отсутствуют обязательные ключи")
            raise ValueError(f"Элемент {idx}: отсутствуют обязательные ключи")

        # Пробуем привести значения ключей к нужным типам
        try:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
            price = float(item["price"])
        except (ValueError, TypeError) as e:
            logger.error(f"Элемент {idx}: некорректные типы данных")
            raise ValueError(f"Элемент {idx}: некорректные типы данных") from e

        # Проверяем, что количество товара больше 0
        if quantity < 1:
            logger.error(f"Элемент {idx}: количество должно быть больше 0")
            raise ValueError(f"Элемент {idx}: некорректное количество")
        # Проверяем, что цена не является отрицательной
        if price < 0:
            logger.error(f"Элемент {idx}: цена не может быть отрицательной")
            raise ValueError(f"Элемент {idx}: некорректная цена")

    # Составляем список идентификаторов товаров
    # для проверки их существования в базе
    product_ids = [item["product_id"] for item in items]
    try:
        # Формируем запрос для выборки всех товаров с указанными product_id
        result = await session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        )
        # Создаем множество существующих идентификаторов товаров
        existing_ids = {row for row in result.scalars()}
    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка проверки товаров: {str(e)}")
        raise RuntimeError("Ошибка проверки товаров") from e

    # Вычисляем множество идентификаторов, которых нет в базе
    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Не найдены товары с ID: {missing_ids}")
        raise ValueError(f"Несуществующие товары: {missing_ids}")

    # Формируем данные для массовой вставки в таблицу OrderItem
    insert_data = [
        {
            "order_id": order_id,
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": item["price"],
        }
        for item in items
    ]

    # Массовая вставка данных в рамках транзакции
    try:
        async with session.begin():
            await session.execute(insert(OrderItem), insert_data)
        logger.info(f"Успешно добавлено {len(items)}"
                    f" товаров в заказ {order_id}")
        return len(items)

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка добавления товаров: {str(e)}")
        raise RuntimeError("Ошибка добавления товаров") from e
    except Exception as e:
        logger.exception("Неожиданная ошибка при добавлении товаров")
        raise RuntimeError("Внутренняя ошибка сервера") from e
