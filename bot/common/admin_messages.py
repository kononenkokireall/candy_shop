import logging
from typing import Tuple

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.formatting import (
    Bold,
    as_list,
    as_marked_section,
    TextLink,
    Underline
)

from database.models import Order
from keyboards.linline_admin import build_admin_keyboard

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def format_order_notification(order: Order) -> Tuple[str, InlineKeyboardMarkup]:
    """Форматирование уведомления о заказе с автоматическим экранированием и добавлением клавиатуры"""
    try:
        if not order:
            return "⚠️ Заказ не найден", build_admin_keyboard(0)

        user = order.user
        if not user:
            return "⚠️ Пользователь не найден", build_admin_keyboard(order.id)

        message_text = as_list(
            as_marked_section(
                Bold("🔥 Новый заказ!"),
                f"#{order.id}",
                marker="▫️ ",
            ),
            as_marked_section(
                Bold("👤 Пользователь:"),
                TextLink(
                    user.first_name or "Без имени",
                    url=f"tg://user?id={user.user_id}"
                ),
                f"Телефон: {user.phone or 'не указан'}",
                marker="  ▪️ ",
            ),
            as_marked_section(
                Bold("📦 Состав заказа:"),
                *[
                    f"{item.product.name} x{item.quantity} - {item.price:.2f} PLN"
                    if item.product
                    else f"Удалённый товар (ID: {item.product_id})"
                    for item in order.items
                ],
                marker="  ▪️ ",
            ),
            as_marked_section(
                Underline("Итого:"),
                f"{order.total_price:.2f} PLN",
                Bold(order.status),
                marker="▫️ ",
            ),
            sep="\n"
        ).as_html()

        keyboard = build_admin_keyboard(order.id)
        return message_text, keyboard

    except Exception as e:
        logger.error(f"Ошибка форматирования уведомления: {e}", exc_info=True)
        return "Ошибка форматирования уведомления", build_admin_keyboard(order.id)