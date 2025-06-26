from typing import Dict, Iterable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import Sequence
from typing_extensions import Literal


# Определение структуры данных для callback-данных меню.
# Класс MenuCallBack наследуется от
# CallbackData и добавляет префикс "menu" к callback-данным.
class MenuCallBack(CallbackData, prefix="menu"):
    level: int  # Уровень вложенности меню.

    menu_name: str  # Название текущего меню,
    # Используется для определения контекста.
    # Идентификатор категории, если применяется. По умолчанию None.
    category: int | None = None
    page: int | None = None
    # Номер страницы меню.
    # Используется для пагинации, по умолчанию равен 1.
    product_id: int | None = None

    # Идентификатор продукта,
    # если требуется. По умолчанию None.

    # Валидатор для поля level, чтобы гарантировать,
    # что уровень не является отрицательным.
    def __post_init__(self) -> None:  # noqa: D401
        if self.lvl < 0:
            raise ValueError("lvl must be ≥ 0")


# Определение структуры данных для callback-данных,
# связанных с действиями по заказу.
# Префикс "order" будет автоматически добавлен к callback-данным.
class OrderCallbackData(CallbackData, prefix="order"):
    action: Literal["c", "x"]  # Действие, связанное с заказом
    oid: int


# Функция для создания основной inline-клавиатуры для пользователя.
def get_user_main_btn(
        *,
        level: int,
        row_sizes: Sequence[int] | int = (2,),
) -> InlineKeyboardMarkup:
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

    if isinstance(row_sizes, int):
        row_sizes = (row_sizes,)  # число → кортеж
    elif not isinstance(row_sizes, Iterable):
        row_sizes = (2,)

        # Создаем объект билдера для inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # Определяем словарь с текстами кнопок и соответствующими именами меню.
    buttons = {
        "Товары 🍭 💨": ("catalog", level + 1),
        "Корзина 🛒": ("cart", level + 1),
        "О нас 💬": ("about", level),
        "Оплата 💳": ("payment", level),
        "Доставка 📦": ("shipping", level),
    }

    for text, (manu_name, btn_level) in buttons.items():
        keyboard.button(
            text=text,
            callback_data=MenuCallBack(level=btn_level, menu_name=manu_name).pack()
        )

    keyboard.adjust(*row_sizes)
    return keyboard.as_markup()


# Универсальная функция для создания inline-клавиатуры из словаря.
def get_callback_btn(
        *,
        btn: Dict[str, str],
        row_sizes: tuple[int, ...] = (2,)
) -> InlineKeyboardMarkup:
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
    for txt, data in btn.items():
        assert len(data) <= 60, "callback too long!"
        keyboard.button(text=txt, callback_data=data)
    keyboard.adjust(*row_sizes)
    return keyboard.as_markup()
