from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OrderAction(CallbackData, prefix="order"):
    action: str  # confirm/cancel
    order_id: int


def build_admin_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Построение клавиатуры для администратора"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=OrderAction(
                action="confirm",
                order_id=order_id
            ).pack()
        ),
        InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data=OrderAction(
                action="cancel",
                order_id=order_id
            ).pack()
        )
    )
    return keyboard.as_markup()