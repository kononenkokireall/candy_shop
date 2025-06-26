import logging
from contextlib import suppress
from typing import Tuple

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.admin_messages import format_order_notification
from common.user_message import format_user_response
from database.engine import session_maker
from database.models import Order, OrderItem, OrderStatus, Product
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
) -> tuple[InputMediaPhoto, InlineKeyboardMarkup]:
    """
    Создаёт заказ из корзины пользователя и возвращает (media, keyboard).
    *Не* делает commit/rollback – это обязанность middleware.
    При любой ошибке возвращает дефолтный баннер-ошибку + пустую клавиатуру.
    """
    # ---------- дефолтный ответ (ошибка / пустая корзина) -----------------
    default_resp: tuple[InputMediaPhoto, InlineKeyboardMarkup] = (
        InputMediaPhoto(
            media="static/banners/error_order.jpg",
            caption="Ошибка оформления заказа!",
        ),
        InlineKeyboardMarkup(inline_keyboard=[]),
    )

    # ---------- читаем корзину -------------------------------------------
    carts = await orm_get_user_carts(session, user_id)
    if not carts:
        logger.warning("Корзина пользователя %s пуста", user_id)
        return default_resp

    total_price = sum(c.quantity * c.product.price for c in carts)

    try:
        # ---------- 1. создаём заказ --------------------------------------
        order = Order(
            user_id=user_id,
            total_price=total_price,
            status=OrderStatus.PENDING,
        )
        session.add(order)
        await session.flush()  # → order.id заполнился
        for c in carts:
            product: Product = c.product  # связан уже при запросе
            if product.stock < c.quantity:  # нет нужного кол-ва
                raise ValueError(
                    f"Товара «{product.name}» осталось {product.stock} шт."
                )
            product.stock -= c.quantity
            # ---------- 2. добавляем позиции ---------------------------------
        order_items = [
            OrderItem(
                order_id=order.id,
                product_id=c.product_id,
                product_name=c.product.name or f"ID #{c.product_id}",
                quantity=c.quantity,
                price=c.product.price,
            )
            for c in carts
        ]
        session.add_all(order_items)

        # ---------- 3. очищаем корзину -----------------------------------
        for c in carts:
            await orm_full_remove_from_cart(session, user_id, c.product_id)
        await session.commit()

        # ---------- 4. формируем ответ пользователю ----------------------
        banner = await orm_get_banner(session, "order")
        user_resp = format_user_response(banner, total_price, order_items)

    except SQLAlchemyError as db_err:
        logger.error("DB-ошибка при оформлении заказа: %s", db_err,
                     exc_info=True)
        return default_resp
    except Exception as err:
        logger.error("Ошибка checkout(): %s", err, exc_info=True)
        return default_resp

    # ---------- уведомляем админа (best-effort) ---------------------------
    with suppress(Exception):
        admin_text, admin_kb = await format_admin_notification(order.id)
        await notification_service.send_to_admin(
            text=admin_text,
            reply_markup=admin_kb,
            parse_mode="HTML",
        )

    logger.info("Заказ %s пользователя %s оформлен", order.id, user_id)
    return user_resp


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
