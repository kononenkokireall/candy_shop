
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order
from database.orm_querys.orm_query_order import orm_add_order_items


######################## Работа с заказами #######################################

async def orm_create_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        address: str | None = None,
        phone: str | None = None,
        status: str = "pending"
):
    """Создаёт заказ и возвращает объект заказа."""
    order = Order(
        user_id=user_id,
        total_price=total_price,
        status=status,
        address=address,
        phone=phone
    )
    session.add(order)
    await session.flush()  # Получаем order.id
    return order



async def orm_add_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: list[dict],
        address: str | None = None,
        phone: str | None = None,
        status: str = "pending"
):
    """Создаёт заказ и добавляет в него товары."""
    try:
        order = await orm_create_order(
            session,
            user_id,
            total_price,
            address,
            phone,
            status
        )
        await orm_add_order_items(session, order.id, items)
        await session.commit()
        return order
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"Ошибка при создании заказа: {str(e)}")


