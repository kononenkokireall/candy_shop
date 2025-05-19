import logging
from typing import Optional, List, Dict, Sequence

from sqlalchemy import select, update, delete, exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Product, Order, OrderItem

# Настраиваем логгер для данного модуля
logger = logging.getLogger(__name__)


# Создает новый заказ с полной валидацией и обработкой ошибок.
async def orm_create_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: List[Dict],
        address: Optional[str] = None,
        phone: Optional[str] = None,
        status: str = "pending",
) -> Order:
    """
    Создает новый заказ с полной валидацией и обработкой ошибок.

    Параметры:
      - session: Асинхронная сессия БД.
      - user_id: Идентификатор пользователя, который оформляет заказ.
      - total_price: Общая сумма заказа.
      - items: Список товаров в заказе. Каждый элемент должен быть словарем,
       содержащим
               ключи "product_id", "quantity" и "price".
      - address: (Опционально) Адрес доставки.
      - phone: (Опционально) Телефон для связи.
      - status: Статус заказа (по умолчанию "pending").

    Возвращает:
      - Order: Созданный объект заказа.

    Исключения:
      - ValueError: Если входные данные (items) некорректны.
      - RuntimeError: Если происходит ошибка работы с базой данных.
    """
    logger.info(f"Создание заказа для пользователя {user_id}")

    # Валидация входных данных: items должен быть списком словарей
    if not isinstance(items, list) or not all(isinstance(item, dict)
                                              for item in items):
        logger.error("Некорректный формат items: должен быть список словарей")
        raise ValueError("Items должен быть списком словарей")

    # Проверяем, что каждый словарь содержит необходимые ключи
    required_keys = {"product_id", "quantity", "price"}
    for idx, item in enumerate(items, 1):
        missing = required_keys - item.keys()
        if missing:
            logger.error(f"Элемент {idx}: отсутствуют ключи {missing}")
            raise ValueError(f"Элемент {idx}: отсутствуют ключи {missing}")

        # Проверяем, что количество товара больше 0
        if item["quantity"] < 1:
            logger.error(f"Элемент {idx}: некорректное количество")
            raise ValueError(f"Элемент {idx}: количество должно быть больше 0")

        # Проверяем, что цена товара положительная
        if item["price"] <= 0:
            logger.error(f"Элемент {idx}: некорректная цена")
            raise ValueError(f"Элемент {idx}: цена должна быть больше 0")

    # Проверка существования товаров в базе
    product_ids = [item["product_id"] for item in items]
    try:
        # Формируем запрос на выборку идентификаторов продуктов,
        # которые есть в базе
        existing = await session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        )
        # Собираем все существующие идентификаторы в множество
        existing_ids = {row for row in existing.scalars()}
    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка проверки товаров: {str(e)}")
        raise RuntimeError("Ошибка проверки товаров") from e

    # Определяем, какие товары отсутствуют в базе
    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Не найдены товары с ID: {missing_ids}")
        raise ValueError(f"Несуществующие товары: {missing_ids}")

    # Создание заказа в рамках транзакции
    try:
        #async with session.begin():
            # Создаем основной объект заказа
            order = Order(
                user_id=user_id,
                total_price=total_price,
                status=status,
                address=address,
                phone=phone,
            )
            session.add(order)
            # Выполняем flush для получения сгенерированного идентификатора
            # заказа (order.id)
            await session.flush()

            # Формируем список объектов OrderItem
            # на основе каждого элемента items
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                )
                for item in items
            ]
            # Добавляем все позиции заказа в сессию
            session.add_all(order_items)

            logger.info(f"Заказ {order.id} успешно создан с"
                        f" {len(items)} позициями")
            return order

    except exc.SQLAlchemyError as e:
        logger.exception(f"Ошибка создания заказа: {str(e)}")
        raise RuntimeError("Ошибка создания заказа") from e


# Функция Получает список заказов пользователя с поддержкой пагинации.
async def orm_get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Order]:
    """
    Получает список заказов пользователя с поддержкой пагинации.

    Параметры:
      - session: Асинхронная сессия БД.
      - user_id: Идентификатор пользователя.
      - limit: Максимальное количество записей, возвращаемых запросом.
      - offset: Смещение выборки (для реализации пагинации).

    Возвращает:
      - Sequence[Order]: Список заказов пользователя с загруженными элементами.
    """
    logger.debug(
        f"Получение заказов пользователя {user_id} [limit={limit},"
        f" offset={offset}]"
    )

    try:
        # Формируем запрос: выбираем заказы для данного пользователя,
        # сортируем по дате создания (по убыванию),
        # добавляем опцию пред загрузки позиций заказа (Order.items)
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created.desc())
            .limit(limit)
            .offset(offset)
        )
        # Возвращаем уникальные заказы
        return result.unique().scalars().all()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения заказов: {str(e)}")
        raise RuntimeError("Ошибка получения заказов") from e


# Функция Получает полную информацию о заказе,
# включая позиции и связанные данные о товарах.
async def orm_get_order_details(
        session: AsyncSession,
        order_id: int
) -> Optional[Order]:
    """
    Получает полную информацию о заказе,
     включая позиции и связанные данные о товарах.

    Параметры:
      - session: Асинхронная сессия БД.
      - order_id: Идентификатор заказа, детали которого необходимо получить.

    Возвращает:
      - Optional[Order]: Объект заказа с загруженными данными или None,
       если заказ не найден.
    """
    logger.debug(f"Получение деталей заказа {order_id}")

    try:
        # Формируем запрос для получения заказа по его ID с
        # загрузкой позиций (Order.items)
        # и связанных данных о товарах (joinedload для OrderItem.product)
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items).joinedload(OrderItem.product))
        )
        return result.scalar_one_or_none()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения заказа {order_id}: {str(e)}")
        raise RuntimeError("Ошибка получения деталей заказа") from e


# Функция Обновляет статус заказа.
async def orm_update_order_status(
        session: AsyncSession,
        order_id: int,
        new_status: str
) -> bool:
    """
    Обновляет статус заказа.

    Параметры:
      - session: Асинхронная сессия БД.
      - order_id: Идентификатор заказа.
      - new_status: Новый статус заказа.

    Возвращает:
      - bool: True, если обновление прошло успешно;
       False, если заказ не найден.
    """
    logger.info(f"Обновление статуса заказа {order_id} -> {new_status}")

    try:
        result = await session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=new_status)
            .returning(Order.id)
        )
        updated = result.scalar_one_or_none()
        await session.commit()
        return bool(updated)

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка обновления статуса: {str(e)}")
        raise RuntimeError("Ошибка обновления статуса заказа") from e


# Функция Удаляет заказ и все связанные с ним элементы (позиции заказа).
async def orm_delete_order(
        session: AsyncSession,
        order_id: int
) -> bool:
    """
    Удаляет заказ и все связанные с ним элементы (позиции заказа).

    Параметры:
      - session: Асинхронная сессия БД.
      - order_id: Идентификатор заказа для удаления.

    Возвращает:
      - bool: True, если удаление прошло успешно; False, если заказ не найден.
    """
    logger.warning(f"Попытка удаления заказа {order_id}")

    try:
        # Удаляем позиции заказа
        await session.execute(
            delete(OrderItem).where(OrderItem.order_id == order_id)
        )

        # Удаляем сам заказ
        result = await session.execute(
            delete(Order).where(Order.id == order_id).returning(Order.id)
        )

        await session.commit()
        return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка удаления заказа: {str(e)}")
        raise RuntimeError("Ошибка удаления заказа") from e

