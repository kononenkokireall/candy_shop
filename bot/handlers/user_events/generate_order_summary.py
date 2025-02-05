from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

# Импортируем запросы ORM, Models для работы с БД
from database.models import Order, OrderItem
from database.orm_querys_order.orm_query_create_order import orm_get_banner


# Функция генерации текста с деталями заказа
async def generate_order_summary(order_id: int, session: AsyncSession) -> str:
    """Генерирует текст с деталями заказа"""
    order = await session.get(Order, order_id)
    items = await session.execute(
        select(OrderItem)
        .where(OrderItem.order_id == order_id)
        .options(joinedload(OrderItem.product))
    )
    items = items.scalars().all()

    payment_info = await orm_get_banner(session, "payment_info")

    summary = (
        "📝 *Детали вашего заказа:*\n\n"
        "🛒 *Состав заказа:*\n"
    )

    for item in items:
        summary += f"• {item.product.name} - {item.quantity} шт. × {item.product.price} PLN\n"

    summary += (
        f"\n💵 *Итого к оплате:* {order.total_price} PLN\n\n"
        f"💳 *Способы оплаты:*\n{payment_info.description}\n\n"
        "📦 *Условия доставки:*\n"
        "Доставка осуществляется в течение 2-3 рабочих дней. "
        "Самовывоз доступен из нашего офиса по адресу: ..."
    )

    return summary
