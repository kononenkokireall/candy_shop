from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_callback_btn(*, btn: dict[str,str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    for text, data  in btn.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(*sizes).as_markup()