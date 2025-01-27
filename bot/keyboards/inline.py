from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class MenuCallBack(CallbackData, prefix="menu"):
    level: int
    menu_name: str
    category: int | None = None


def get_user_main_btn(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btn = {
        "Товары 🍭|💨": "catalog",
        "Корзина 🛒": "cart",
        "О нас 💬": "about",
        "Оплата 💳": "payment",
        "Доставка 📦": "shipping",
    }
    for text, menu_name in btn.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(
                text=text, callback_data=MenuCallBack(level=level+1, menu_name=menu_name).pack()
            ))
        elif menu_name == 'cart':
            keyboard.add(InlineKeyboardButton(
                text=text, callback_data=MenuCallBack(level=3, menu_name=menu_name).pack()
            ))
        else:
            keyboard.add(InlineKeyboardButton(
                text=text, callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()
            ))
    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_btn(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="Назад", callback_data=MenuCallBack(level=level-1, menu_name='main').pack()
    ))
    keyboard.add(InlineKeyboardButton(
        text="Корзина 🛒", callback_data=MenuCallBack(level=3, menu_name='cart').pack()
    ))

    for ctg in categories:
        keyboard.add(InlineKeyboardButton(
            text=ctg.name, callback_data=MenuCallBack(level=level+1, menu_name=ctg.name, category=ctg.id).pack()
        ))
    return keyboard.adjust(*sizes).as_markup()


def get_callback_btn(*, btn: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btn.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
