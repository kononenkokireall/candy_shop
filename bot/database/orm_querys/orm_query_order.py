import logging
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Product, Order, OrderItem

# Настройка логгера
logger = logging.getLogger(__name__)


# Создание заказа
async def orm_add_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: list[dict],
        address: str | None = None,
        phone: str | None = None,
        status: str = "pending"
):
    """
    Создает новый заказ. Проверяет корректность данных и существование товаров.
    """
    logger.info(f"Создание заказа для пользователя {user_id} на сумму {total_price}")

    if not isinstance(items, list):
        logger.error("Ошибка: items должен быть списком")
        raise ValueError("items должен быть списком")

    for item in items:
        if not all(key in item for key in ("product_id", "quantity", "price")):
            logger.error("Ошибка: Неверная структура items")
            raise ValueError("Каждый элемент items должен содержать product_id, quantity и price")

        if item["quantity"] < 1:
            logger.error(f"Ошибка: Некорректное количество для продукта {item['product_id']}")
            raise ValueError(f"Некорректное количество для продукта {item['product_id']}")

        if item["price"] < 0:
            logger.error(f"Ошибка: Некорректная цена для продукта {item['product_id']}")
            raise ValueError(f"Некорректная цена для продукта {item['product_id']}")

    # Проверяем существование товаров
    product_ids = [item["product_id"] for item in items]
    existing_products = await session.execute(select(Product.id).where(Product.id.in_(product_ids)))
    existing_ids = {row[0] for row in existing_products.all()}

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        logger.error(f"Ошибка: Товары с ID {missing_ids} не найдены")
        raise ValueError(f"Товары с ID {missing_ids} не найдены")

    try:
        # Создаем заказ
        order = Order(
            user_id=user_id,
            total_price=total_price,
            status=status,
            address=address,
            phone=phone
        )
        session.add(order)
        await session.flush()  # Получаем ID заказа
        logger.info(f"Заказ {order.id} создан")

        # Добавляем элементы заказа
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
            session.add(order_item)

        await session.commit()
        logger.info(f"Заказ {order.id} успешно добавлен в базу")
        return order

    except Exception as e:
        await session.rollback()
        logger.exception(f"Ошибка при создании заказа: {str(e)}")
        raise RuntimeError(f"Ошибка при создании заказа: {str(e)}")


async def orm_create_order(session: AsyncSession, data: dict):
    logger.info(f"Создание заказа для пользователя {data['user_id']}")
    order = Order(
        user_id=data["user_id"],
        total_price=data["total_price"]
    )
    session.add(order)
    await session.flush()
    logger.info(f"Заказ {order.id} создан")
    return order


async def orm_add_order_items(session: AsyncSession, order_id: int, items: list):
    logger.info(f"Добавление товаров в заказ {order_id}")
    for item in items:
        order_item = OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        session.add(order_item)
    await session.commit()
    logger.info(f"Товары успешно добавлены в заказ {order_id}")


# Получение заказов пользователя
async def orm_get_user_orders(session: AsyncSession, user_id: int):
    logger.info(f"Запрос списка заказов пользователя {user_id}")
    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.items))
        .order_by(Order.created.desc())
    )
    result = await session.execute(query)
    orders = result.unique().scalars().all()
    logger.info(f"Найдено {len(orders)} заказов для пользователя {user_id}")
    return orders


# Получение деталей конкретного заказа
async def orm_get_order_details(session: AsyncSession, order_id: int):
    logger.info(f"Запрос деталей заказа {order_id}")
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )
    result = await session.execute(query)
    order = result.unique().scalar()
    if order:
        logger.info(f"Заказ {order_id} найден")
    else:
        logger.warning(f"Заказ {order_id} не найден")
    return order


# Обновление статуса заказа
async def orm_update_order_status(session: AsyncSession, order_id: int, new_status: str):
    logger.info(f"Обновление статуса заказа {order_id} на {new_status}")
    query = (
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await session.execute(query)
    await session.commit()
    logger.info(f"Статус заказа {order_id} обновлен на {new_status}")


# Удаление заказа
async def orm_delete_order(session: AsyncSession, order_id: int):
    logger.info(f"Удаление заказа {order_id}")
    query = delete(Order).where(Order.id == order_id)
    await session.execute(query)
    await session.commit()
    logger.info(f"Заказ {order_id} успешно удален")
