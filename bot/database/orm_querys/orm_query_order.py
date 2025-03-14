import logging
from typing import Optional, List, Dict, Sequence

from sqlalchemy import select, update, delete, exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from database.models import Product, Order, OrderItem

logger = logging.getLogger(__name__)


async def orm_create_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: List[Dict],
        address: Optional[str] = None,
        phone: Optional[str] = None,
        status: str = "pending"
) -> Order:
    """
    Создает новый заказ с полной валидацией и обработкой ошибок.

    Параметры:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        total_price: Общая сумма заказа
        items: Список товаров в заказе
        address: Адрес доставки (опционально)
        phone: Телефон для связи (опционально)
        status: Статус заказа (по умолчанию "pending")

    Возвращает:
        Order: Созданный объект заказа

    Исключения:
        ValueError: При некорректных входных данных
        RuntimeError: При ошибках работы с БД
    """
    logger.info(f"Создание заказа для пользователя {user_id}")

    # Валидация входных данных
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        logger.error("Некорректный формат items: должен быть список словарей")
        raise ValueError("Items должен быть списком словарей")

    required_keys = {"product_id", "quantity", "price"}
    for idx, item in enumerate(items, 1):
        missing = required_keys - item.keys()
        if missing:
            logger.error(f"Элемент {idx}: отсутствуют ключи {missing}")
            raise ValueError(f"Элемент {idx}: отсутствуют ключи {missing}")

        if item["quantity"] < 1:
            logger.error(f"Элемент {idx}: некорректное количество")
            raise ValueError(f"Элемент {idx}: количество должно быть больше 0")

        if item["price"] <= 0:
            logger.error(f"Элемент {idx}: некорректная цена")
            raise ValueError(f"Элемент {idx}: цена должна быть больше 0")

    # Проверка существования товаров
    product_ids = [item["product_id"] for item in items]
    try:
        existing = await session.execute(
            select(Product.id).where(Product.id.in_(product_ids))
        )
        existing_ids = {row.id for row in existing.scalars()}
    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка проверки товаров: {str(e)}")
        raise RuntimeError("Ошибка проверки товаров") from e

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Не найдены товары с ID: {missing_ids}")
        raise ValueError(f"Несуществующие товары: {missing_ids}")

    # Создание заказа в транзакции
    try:
        async with session.begin():
            # Создаем основной заказ
            order = Order(
                user_id=user_id,
                total_price=total_price,
                status=status,
                address=address,
                phone=phone
            )
            session.add(order)
            await session.flush()

            # Добавляем элементы заказа
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                for item in items
            ]
            session.add_all(order_items)

            logger.info(f"Заказ {order.id} успешно создан с {len(items)} позициями")
            return order

    except exc.SQLAlchemyError as e:
        logger.exception(f"Ошибка создания заказа: {str(e)}")
        raise RuntimeError("Ошибка создания заказа") from e


async def orm_get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Order]:
    """
    Получает список заказов пользователя с пагинацией

    Параметры:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        limit: Максимальное количество записей
        offset: Смещение выборки

    Возвращает:
        List[Order]: Список заказов с предзагруженными элементами
    """
    logger.debug(f"Получение заказов пользователя {user_id} [limit={limit}, offset={offset}]")

    try:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items))
            .order_by(Order.created.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.unique().scalars().all()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения заказов: {str(e)}")
        raise RuntimeError("Ошибка получения заказов") from e


async def orm_get_order_details(session: AsyncSession, order_id: int) -> Optional[Order]:
    """
    Получает полную информацию о заказе

    Параметры:
        session: Асинхронная сессия БД
        order_id: ID заказа

    Возвращает:
        Optional[Order]: Объект заказа или None если не найден
    """
    logger.debug(f"Получение деталей заказа {order_id}")

    try:
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).joinedload(OrderItem.product)
            )
        )
        return result.scalar_one_or_none()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения заказа {order_id}: {str(e)}")
        raise RuntimeError("Ошибка получения деталей заказа") from e


async def orm_update_order_status(
        session: AsyncSession,
        order_id: int,
        new_status: str
) -> bool:
    """
    Обновляет статус заказа

    Параметры:
        session: Асинхронная сессия БД
        order_id: ID заказа
        new_status: Новый статус

    Возвращает:
        bool: True если обновление успешно, False если заказ не найден
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

        if updated:
            await session.commit()
            return True
        return False

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка обновления статуса: {str(e)}")
        raise RuntimeError("Ошибка обновления статуса заказа") from e


async def orm_delete_order(session: AsyncSession, order_id: int) -> bool:
    """
    Удаляет заказ и связанные элементы

    Параметры:
        session: Асинхронная сессия БД
        order_id: ID заказа

    Возвращает:
        bool: True если удаление успешно, False если заказ не найден
    """
    logger.warning(f"Попытка удаления заказа {order_id}")

    try:
        async with session.begin():
            # Удаление связанных элементов заказа
            await session.execute(
                delete(OrderItem)
                .where(OrderItem.order_id == order_id)
            )

            # Удаление основного заказа
            result = await session.execute(
                delete(Order)
                .where(Order.id == order_id)
                .returning(Order.id)
            )
            return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка удаления заказа: {str(e)}")
        raise RuntimeError("Ошибка удаления заказа") from e