import logging
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Order
from database.orm_querys.orm_query_order import orm_add_order_items

# Настраиваем логгер
logger = logging.getLogger(__name__)


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
    logger.info(f"Создание заказа для пользователя {user_id} на сумму {total_price}")

    order = Order(
        user_id=user_id,
        total_price=total_price,
        status=status,
        address=address,
        phone=phone
    )
    session.add(order)
    await session.flush()  # Получаем order.id

    logger.debug(f"Заказ создан с ID {order.id}")
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
    logger.info(f"Начало оформления заказа для пользователя {user_id}")

    try:
        order = await orm_create_order(
            session,
            user_id,
            total_price,
            address,
            phone,
            status
        )

        logger.debug(f"Добавление товаров в заказ {order.id}")
        await orm_add_order_items(session, order.id, items)

        await session.commit()
        logger.info(f"Заказ {order.id} успешно оформлен для пользователя {user_id}")

        return order

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при создании заказа для {user_id}: {str(e)}", exc_info=True)
        raise RuntimeError(f"Ошибка при создании заказа: {str(e)}")
