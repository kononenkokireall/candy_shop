from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_keyboard(*btn: str, placeholder: str = None,
                 request_contact = None, request_location = None, sizes: tuple = (2, 2)):
    """Parameters request_contact and request_location must be as indexes of btn args
    for buttons you need.
    Example:
        Меню,
        О магазине,
        Варианты оплаты,
        Варианты доставки,
    """
    keyboard = ReplyKeyboardBuilder()
    for index, text in enumerate(btn, start=0):
        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        elif request_location and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(resize_keyboard=True,
                                                     input_field_placeholder=placeholder)