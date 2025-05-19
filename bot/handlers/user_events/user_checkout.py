import logging
from typing import Tuple

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.admin_messages import format_order_notification
from common.user_message import format_user_response
from database.engine import session_maker
from database.models import Order, OrderItem
from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_cart import orm_get_user_carts, \
    orm_full_remove_from_cart
from utilit.notification import NotificationService

# Настройка базового логирования для всего модуля
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Функция Обрабатывает оформление заказа пользователя.
async def checkout(
        session: AsyncSession,
        user_id: int,
        notification_service: NotificationService,
) -> Tuple[InputMediaPhoto, InlineKeyboardMarkup]:
    """
    Обрабатывает оформление заказа пользователя.

    Возвращает:
      - Кортеж из InputMediaPhoto и InlineKeyboardMarkup с информацией о заказе.
      - В случае ошибки возвращает сообщение о неудаче.
    """

    # Ответ по умолчанию при ошибке
    user_content = (
        InputMediaPhoto(
            media="default_banner.jpg", caption="Ошибка оформления заказа!"
        ),
        InlineKeyboardMarkup(inline_keyboard=[]),
    )

    try:
        logger.info(f"Начало оформления заказа для пользователя {user_id}")

        # Получаем корзину пользователя
        carts_user = await orm_get_user_carts(session, user_id)
        if not carts_user:
            logger.warning(f"Корзина пользователя {user_id} пуста")
            return user_content

        # Расчёт общей стоимости
        total_price = sum(
            item.quantity * item.product.price for item in carts_user)

        # Создание заказа и позиций
        order = Order(user_id=user_id, total_price=total_price,
                      status="pending")
        session.add(order)
        await session.flush()  # Получаем order.id

        order_items = [
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price,
            )
            for item in carts_user
        ]
        session.add_all(order_items)

        # Удаляем товары из корзины
        for item in carts_user:
            await orm_full_remove_from_cart(session, user_id, item.product_id)

        # Завершаем транзакцию — заказ оформлен
        await session.commit()
        logger.info(
            f"Заказ {order.id} пользователя {user_id} оформлен успешно")

    except SQLAlchemyError as db_err:
        logger.error(f"Ошибка при работе с БД: {db_err}", exc_info=True)
        await session.rollback()
        return user_content

    # НЕ транзакционные операции — безопасны и изолированы
    try:
        # Получаем баннер отдельно (не обязательно в транзакции)
        banner = await orm_get_banner(session, "order")

        # Формируем ответ пользователю
        user_content = format_user_response(banner, total_price, order_items)

    except Exception as format_err:
        logger.error(
            f"Ошибка при подготовке ответа пользователю: {format_err}",
            exc_info=True)
        return user_content

    try:
        admin_text, admin_keyboard = await format_admin_notification(order.id)
        await notification_service.send_to_admin(
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode="HTML"
        )
    except Exception as notify_err:
        logger.warning(
            f"Ошибка при отправке уведомления администратору: {notify_err}")

    return user_content


# Функция Форматирует уведомление для администратора о новом заказе.
async def format_admin_notification(
        order_id: int
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Форматирует уведомление для администратора о новом заказе.

    Аргументы:
      - order_id: Идентификатор заказа, для которого формируется уведомление.

    Возвращает:
      - Кортеж из строки (сообщение)
       и InlineKeyboardMarkup (клавиатура для взаимодействия с уведомлением).
    """
    try:
        # Создаем новую асинхронную сессию для работы с БД
        async with session_maker() as session:
            # Формируем запрос для получения заказа
            # с загрузкой связанных данных:
            # - Пользователя, связанного с заказом
            # - Элементов заказа с загрузкой информации о товаре
            stmt = (
                select(Order)
                .options(
                    # Пред загрузка данных о пользователе
                    selectinload(Order.user),
                    selectinload(Order.items).selectinload(
                        OrderItem.product
                    ),  # Пред загрузка данных о каждом товаре
                )
                .where(Order.id == order_id)  # Фильтр по идентификатору заказа
            )

            # Выполняем запрос
            result = await session.execute(stmt)
            order = result.scalars().first()

            # Форматируем сообщение
            # с использованием функции форматирования уведомлений
            if order:
                return format_order_notification(order)
            else:
                logger.error(f"Ошибка: заказ {order_id} не найден")
                return ("Ошибка: заказ не найден",
                        InlineKeyboardMarkup(inline_keyboard=[]))

    except Exception as e:
        # Логируем ошибку при форматировании уведомления для заказа
        logging.error(
            f"Ошибка при форматировании уведомления для заказа "
            f"{order_id}: {e}",
            exc_info=True, )
        raise
