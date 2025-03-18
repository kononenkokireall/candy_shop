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
from database.orm_querys.orm_query_cart import orm_get_user_carts, \
    orm_delete_from_cart
from utilit.notification import NotificationService

# Настройка базового логирования для всего модуля
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def checkout(
        session: AsyncSession,
        user_id: int,
        notification_service: NotificationService
) -> Tuple[InputMediaPhoto, InlineKeyboardMarkup]:
    """
    Обрабатывает оформление заказа пользователя.

    Параметры:
      - session: Асинхронная сессия SQLAlchemy для работы с БД.
      - user_id: Идентификатор пользователя, для которого оформляется заказ.
      - notification_service: Сервис для отправки уведомлений администратору.

    Возвращает:
      - Кортеж, состоящий из InputMediaPhoto и InlineKeyboardMarkup,
       которые будут отправлены пользователю.
        В случае ошибки возвращается сообщение об ошибке оформления заказа.
    """
    # Значение по умолчанию для ответа (ошибка оформления заказа)
    user_content = (
        InputMediaPhoto(
            media="default_banner.jpg", caption="Ошибка оформления заказа!"
        ),
        InlineKeyboardMarkup(inline_keyboard=[]),
    )

    try:
        logger.info(f"Начало оформления заказа для пользователя {user_id}")

        # Открываем транзакцию с использованием асинхронного контекста
        async with session.begin():
            # Загружаем баннер для оформления заказа
            # (например, для отображения в чате)
            banner = await orm_get_banner(session, "order")
            # Получаем все товары, добавленные пользователем в корзину
            carts_user = await orm_get_user_carts(session, user_id)

            # Если корзина пуста, логируем предупреждение и
            # возвращаем стандартное сообщение об ошибке
            if not carts_user:
                logger.warning(f"Корзина пользователя {user_id} пуста")
                return user_content

            # Расчет общей стоимости заказа по сумме:
            # количество * цена для каждого товара в корзине
            total_price = sum(
                item.quantity * item.product.price for item in carts_user)
            # Создаем объект заказа с указанием пользователя,
            # общей стоимостью и статусом "pending"
            order = Order(user_id=user_id, total_price=total_price,
                          status="pending")
            session.add(order)
            # Выполняем flush, чтобы получить
            # ID созданного заказа до коммит транзакции
            await session.flush()

            # Формируем список объектов OrderItem для каждого товара в корзине
            order_items = [
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                for item in carts_user
            ]
            # Добавляем все элементы заказа в сессию
            session.add_all(order_items)

            # Удаляем товары из корзины после создания заказа
            await orm_delete_from_cart(session, user_id)

        # После успешного коммит транзакции отправляем
        # уведомление администратору
        admin_text, admin_keyboard = await format_admin_notification(order.id)
        await notification_service.send_to_admin(
            text=admin_text, reply_markup=admin_keyboard, parse_mode="HTML"
        )

        # Обновляем данные баннера и
        # получаем актуальное состояние корзины (если требуется)
        async with session.begin():
            await session.refresh(banner)
            refreshed_carts = await orm_get_user_carts(session, user_id)

        # Формируем финальное сообщение
        # для пользователя с использованием данных заказа
        user_content = format_user_response(banner, total_price, order_items)

        logger.info(f"Заказ для пользователя {user_id} успешно оформлен")
        return user_content

    except Exception as e:
        # Логирование ошибки с подробной информацией и откат транзакции
        logger.error(f"Ошибка оформления заказа: {e}", exc_info=True)
        await session.rollback()
        return user_content


async def format_admin_notification(
        order_id: int) -> tuple[str, InlineKeyboardMarkup]:
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
            return format_order_notification(order)

    except Exception as e:
        # Логируем ошибку при форматировании уведомления для заказа
        logging.error(
            f"Ошибка при форматировании уведомления для заказа "
            f"{order_id}: {e}",
            exc_info=True,
        )
        raise
