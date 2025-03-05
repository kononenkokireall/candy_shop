from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from pydantic.v1 import validator


# Определение структуры данных для меню обратного вызова
class MenuCallBack(CallbackData, prefix="menu"):
    level: int  # Уровень вложенности меню
    menu_name: str  # Название текущего меню
    category: int | None = None  # ID категории (если требуется)
    page: int = 1  # Номер страницы меню
    product_id: int | None = None  # ID продукта (если требуется)

    @validator('level') #TODO
    def validate_level(self, v):
        if v < 0:
            raise ValueError("Level cannot be negative")
        return v


# Определение структуры данных для управления действиями по заказу
class OrderCallbackData(CallbackData, prefix="order"):
    action: str  # Действие — например, "create", "confirm" и т.д.
    user_id: int | None = None  # ID пользователя (если требуется)


# Функция для создания основной клавиатуры пользователя
def get_user_main_btn(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    # Определение кнопок и их назначения
    btn = {
        "Товары 🍭 💨": "catalog",
        "Корзина 🛒": "cart",
        "О нас 💬": "about",
        "Оплата 💳": "payment",
        "Доставка 📦": "shipping",
    }
    # Создание кнопок на основе словаря
    for text, menu_name in btn.items():
        if menu_name == 'catalog':  # Обработка кнопки "Каталог"
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level + 1,
                    menu_name=menu_name).pack()
            ))
        elif menu_name == 'cart':  # Обработка кнопки "Корзина"
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=3,
                    menu_name=menu_name).pack()
            ))
        else:  # Для всех остальных кнопок
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level,
                    menu_name=menu_name).pack()
            ))
    return keyboard.adjust(*sizes).as_markup()


# Универсальная функция для создания произвольной клавиатуры из словаря
def get_callback_btn(*, btn: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btn.items():
        keyboard.add(InlineKeyboardButton(
            text=text,
            callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
