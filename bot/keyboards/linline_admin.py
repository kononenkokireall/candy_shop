from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack
from utilit.config import settings


class OrderAction(CallbackData, prefix="order"):
    action: str  # confirm/cancel/details
    order_id: int


def build_admin_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=OrderAction(
                        action="confirm",
                        order_id=order_id
                    ).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=OrderAction(
                        action="cancel",
                        order_id=order_id
                    ).pack()
                )
            ]
        ]
    )


def build_user_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для пользователя с кнопками:
      - Чат с админом;
      - Возврат в главное меню.
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Чат с админом 💬",
            url=f"tg://user?id={settings.ADMIN_CHAT_ID}"
        ),
        InlineKeyboardButton(
            text="🏠Обратно в меню",
            callback_data=MenuCallBack(level=0, menu_name='main').pack()
        )
    )
    keyboard.adjust(1)
    return keyboard.as_markup()
