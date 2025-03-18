from typing import Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from pydantic.v1 import validator
from typing_extensions import Optional


# Определение структуры данных для callback-данных меню.
# Класс MenuCallBack наследуется от
# CallbackData и добавляет префикс "menu" к callback-данным.
class MenuCallBack(CallbackData, prefix="menu"):
    level: int  # Уровень вложенности меню.
    # Определяет, на каком уровне пользователь находится.
    menu_name: str  # Название текущего меню,
    # Используется для определения контекста.
    # Идентификатор категории, если применяется. По умолчанию None.
    category: Optional[int] = None
    page: int = 1
    # Номер страницы меню.
    # Используется для пагинации, по умолчанию равен 1.
    product_id: Optional[int] = None
    # Идентификатор продукта,
    # если требуется. По умолчанию None.

    # Валидатор для поля level, чтобы гарантировать,
    # что уровень не является отрицательным.
    @validator("level")
    def validate_level(self, v):
        if v < 0:
            raise ValueError("Level cannot be negative")
        return v


# Определение структуры данных для callback-данных,
# связанных с действиями по заказу.
# Префикс "order" будет автоматически добавлен к callback-данным.
class OrderCallbackData(CallbackData, prefix="order"):
    action: str  # Действие, связанное с заказом
    # (например, "create", "confirm" и т.д.).
    user_id: int | None = (
        None  # Идентификатор пользователя, если требуется. По умолчанию None.
    )


# Функция для создания основной inline-клавиатуры для пользователя.
def get_user_main_btn(
        *,
        level: int,
        sizes: tuple[int, ...] = (2,)) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру с основными кнопками главного меню.

    Аргументы:
      - level: текущий уровень меню,
       который используется для формирования callback-данных.
      - sizes: кортеж, определяющий компоновку рядов клавиатуры
       (например, (2,) означает по 2 кнопки в ряду).

    Возвращает:
      - InlineKeyboardMarkup, готовую для отправки пользователю.
    """
    # Создаем объект билдера для inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # Определяем словарь с текстами кнопок и соответствующими именами меню.
    btn = {
        "Товары 🍭 💨": "catalog",
        "Корзина 🛒": "cart",
        "О нас 💬": "about",
        "Оплата 💳": "payment",
        "Доставка 📦": "shipping",
    }

    # Перебираем словарь и создаем для каждой кнопки
    # InlineKeyboardButton с callback-данными.
    for text, menu_name in btn.items():
        if menu_name == "catalog":
            # Если кнопка "Каталог", увеличиваем уровень на 1.
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level + 1, menu_name=menu_name
                    ).pack(),
                )
            )
        elif (
                menu_name == "cart"
        ):  # Если кнопка "Корзина", используем фиксированный уровень 3.
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=3,
                                               menu_name=menu_name).pack(),
                )
            )
        else:  # Для остальных кнопок используем текущий уровень меню.
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=level,
                                               menu_name=menu_name).pack(),
                )
            )

    # Распределяем кнопки по рядам согласно заданным размерам
    # и возвращаем итоговую разметку.
    return keyboard.adjust(*sizes).as_markup() # type : ignore


# Универсальная функция для создания inline-клавиатуры из словаря.
def get_callback_btn(
        *,
        btn: Dict[str, str],
        sizes: tuple[int, ...] = (2,)) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру на основе словаря,
     где ключ — это текст кнопки, а значение — callback-данные.

    Аргументы:
      - btn: словарь, в котором ключи являются текстами кнопок,
       а значения — callback-данными.
      - sizes: кортеж, задающий количество кнопок в каждом ряду.

    Возвращает:
      - InlineKeyboardMarkup, готовую для отправки пользователю.
    """
    # Создаем объект билдера для inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопки в клавиатуру по элементам словаря.
    for text, data in btn.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    # Распределяем кнопки по рядам согласно заданным размерам
    # и возвращаем итоговую разметку.
    return keyboard.adjust(*sizes).as_markup()  # type : ignore
