# Функция создания клавиатуры для обработки оплаты
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Функция для создания клавиатуры подтверждения оплаты
def get_payment_keyboard(order_id: int, user_id=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=f"confirm_order_{order_id}"
        ),
        InlineKeyboardButton(
            text="💬 Связаться с клиентом",
            url=f"tg://user?id={user_id}"
        )
    )
    return keyboard.adjust(1).as_markup()
