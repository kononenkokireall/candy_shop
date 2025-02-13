######################## Работа с заказами #######################################
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Product, Order, OrderItem


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
    # Проверяем структуру `items`
    if not isinstance(items, list):
        raise ValueError("items должен быть списком")

    for item in items:
        if not all(key in item for key in ("product_id", "quantity", "price")):
            raise ValueError("Каждый элемент items должен содержать product_id, quantity и price")

        if item["quantity"] < 1:
            raise ValueError(f"Некорректное количество для продукта {item['product_id']}")

        if item["price"] < 0:
            raise ValueError(f"Некорректная цена для продукта {item['product_id']}")

    # Проверяем существование товаров
    product_ids = [item["product_id"] for item in items]
    existing_products = await session.execute(select(Product.id).where(Product.id.in_(product_ids)))
    existing_ids = {row[0] for row in existing_products.all()}

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:  # Если какой-то товар не существует, выбрасываем исключение
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
        await session.flush()  # Сохраняем изменения и получаем ID заказа

        # Добавляем элементы заказа
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
            session.add(order_item)

        await session.commit()  # Подтверждаем изменения
        return order

    except Exception as e:
        await session.rollback()  # Если произошла ошибка, откатываем изменения
        raise RuntimeError(f"Ошибка при создании заказа: {str(e)}")


async def orm_create_order(session: AsyncSession, data: dict):
    order = Order(
        user_id=data["user_id"],
        total_price=data["total_price"]
    )
    session.add(order)
    await session.flush()
    return order

async def orm_add_order_items(session: AsyncSession, order_id: int, items: list):
    for item in items:
        order_item = OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        session.add(order_item)
    await session.commit()


# Получение заказов пользователя
async def orm_get_user_orders(session: AsyncSession, user_id: int):
    """
    Возвращает список заказов пользователя.
    """
    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.items))
        .order_by(Order.created.desc())  # Сортируем заказы по дате создания (последние выше)
    )
    result = await session.execute(query)
    return result.unique().scalars().all()


# Получение деталей конкретного заказа
async def orm_get_order_details(session: AsyncSession, order_id: int):
    """
    Возвращает данные заказа и связанные с ним товары.
    """
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )
    result = await session.execute(query)
    return result.unique().scalar()


# Обновление статуса заказа
async def orm_update_order_status(session: AsyncSession, order_id: int, new_status: str):
    """
    Изменяет статус заказа.
    """
    query = (
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await session.execute(query)
    await session.commit()


# Удаление заказа
async def orm_delete_order(session: AsyncSession, order_id: int):
    """
    Удаляет заказ из базы данных.
    """
    query = delete(Order).where(Order.id == order_id)
    await session.execute(query)
    await session.commit()