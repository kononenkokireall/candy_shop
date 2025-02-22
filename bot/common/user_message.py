# ------------------------- Форматирование ответов -------------------------
from typing import Tuple

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup

from database.models import Banner, OrderItem
from keyboards.linline_admin import build_user_keyboard


def format_user_response(
    banner: Banner,
    total_price: float,
    order_items: list[OrderItem],
) -> Tuple[InputMediaPhoto, InlineKeyboardMarkup]:
    """Более безопасное форматирование ответа"""
    items_text = "\n".join(
        f"• {item.product.name} (x{item.quantity})"
        for item in order_items
        if item and item.product
    ) or "Нет информации о товарах"

    caption = (
        "🎉 Спасибо за покупку! 🎉\n\n"
        f"Общая сумма заказа: {total_price:.2f} PLN\n\n"
        f"**Купленные товары:**\n{items_text}"
    )

    return (
        InputMediaPhoto(media=banner.image, caption=caption),
        build_user_keyboard()
    )
