from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product, OrderItem


async def orm_add_order_items(
        session: AsyncSession,
        order_id: int,
        items: list[dict]
):
    """Добавляет товары в заказ."""
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
    existing_products = await (session
                               .execute(select(Product.id)
                                        .where(Product.id.in_(product_ids))))
    existing_ids = {row[0] for row in existing_products.all()}

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:
        raise ValueError(f"Товары с ID {missing_ids} не найдены")

    # Добавляем товары в заказ
    session.add_all([
        OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        for item in items
    ])
