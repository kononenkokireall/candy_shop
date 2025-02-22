##############################Handler перехода в чат пользователя с администратором####################################
from typing import Tuple
import logging
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.admin_messages import format_order_notification
from common.user_message import format_user_response
from database.engine import session_maker

from database.models import Order, OrderItem
from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_cart import orm_get_user_carts, orm_delete_from_cart

from utilit.notification import NotificationService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def checkout(
        session: AsyncSession,
        user_id: int,
        notification_service: NotificationService) -> Tuple[InputMediaPhoto, InlineKeyboardMarkup]:
    """
    Оформление заказа и переход в чат с администратором
    """
    try:
        logger.info(f"Начало оформления заказа для пользователя {user_id}")

        async with session.begin():
            # Получаем данные
            logger.debug("Получение баннера заказа")
            banner = await orm_get_banner(session, 'order')
            logger.debug(f"Получение корзины пользователя {user_id}")
            carts_user = await orm_get_user_carts(session, user_id)

            # Проверка пустой корзины
            if not carts_user:
                logger.warning(f"Корзина пользователя {user_id} пуста")
                raise ValueError("Корзина пользователя пуста")

            # Создание заказа
            logger.debug("Расчет общей стоимости заказа")
            total_price = sum(item.quantity * item.product.price for item in carts_user)
            logger.debug("Создание заказа")
            order = Order(
                user_id=user_id,
                total_price=total_price,
                status="pending"
            )
            session.add(order)
            await session.flush()

            # Добавление позиций заказа
            logger.debug("Добавление позиций заказа")
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.product.price
                )
                for item in carts_user
            ]
            session.add_all(order_items)

            # Очистка корзины
            logger.debug(f"Очистка корзины пользователя {user_id}")
            await orm_delete_from_cart(session, user_id)


            # Отправка уведомлений
            logger.debug("Форматирование уведомления для администратора")
            admin_text, admin_keyboard = await format_admin_notification(order.id)
            await notification_service.send_to_admin(
                text=admin_text,
                reply_markup=admin_keyboard,
                parse_mode="HTML"
            )

            logger.debug("Форматирование ответа для пользователя")
            user_content = format_user_response(banner, total_price, order_items)

        logger.info(f"Заказ для пользователя {user_id} успешно оформлен")
        return user_content

    except ValueError as ve:
        logger.error(f"Ошибка валидации: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Ошибка оформления заказа: {e}", exc_info=True)
        raise


async def format_admin_notification(order_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """
    Форматирование уведомления для администратора о новом заказе.

    Args:
        order_id: ID заказа.

    Returns:
        str: Форматированное сообщение для администратора.
    """
    try:
        # Создаем новую сессию
        async with session_maker() as session:
            # Получаем заказ с предварительной загрузкой связанных данных
            stmt = (
                select(Order)
                .options(
                    selectinload(Order.user),  # Загружаем пользователя
                    selectinload(Order.items).selectinload(OrderItem.product),  # Загружаем товары
                )
                .where(Order.id == order_id)  # Фильтруем по ID заказа
            )

            # Выполняем запрос
            result = await session.execute(stmt)
            order = result.scalars().first()

            # Форматируем сообщение с использованием импортированной функции
            return format_order_notification(order)

    except Exception as e:
        logging.error(f"Ошибка при форматировании уведомления для заказа #{order_id}: {e}", exc_info=True)
        raise


##############################Handler текста с деталями заказа для пользователя########################################