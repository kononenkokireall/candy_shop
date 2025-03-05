# Функция для создания клавиатуры раздела каталога
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для создания клавиатуры каталога
def get_user_catalog_btn(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    # Добавление кнопки "Назад"
    keyboard.add(InlineKeyboardButton(
        text="◀️Вернутся",
        callback_data=MenuCallBack(
            level=level - 1,
            menu_name='main').pack()
    ))
    # Добавление кнопки "Корзина"
    keyboard.add(InlineKeyboardButton(
        text="Корзина 🛒",
        callback_data=MenuCallBack(
            level=3,
            menu_name='cart').pack()
    ))

    # Добавление кнопок на основе категорий
    for ctg in categories:
        keyboard.add(InlineKeyboardButton(
            text=ctg.name,
            callback_data=MenuCallBack(
                level=level + 1,
                menu_name=ctg.name,
                category=ctg.id).pack()
        ))
    return keyboard.adjust(*sizes).as_markup()
