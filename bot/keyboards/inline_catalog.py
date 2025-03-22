from itertools import product
from typing import List, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для создания клавиатуры раздела каталога.
def get_user_catalog_btn(
        *,
        level: int,
        categories: List[Any],
        sizes: tuple[int, ...] = (2,))\
        -> InlineKeyboardMarkup:

    """
    Создает inline-клавиатуру для каталога товаров, включающую кнопки "Назад",
     "Корзина"
    и кнопки для каждой категории из переданного списка.

    Параметры:
      - level: текущий уровень меню,
       используется для формирования callback-данных.
      - categories: список объектов категорий.
       Каждый объект должен иметь атрибуты:
                    - name: текстовое название категории,
                     которое отображается на кнопке;
                    - id: идентификатор категории,
                     передается в callback-данных.
      - sizes: кортеж,
       определяющий расположение кнопок
        (например, (2,) означает по 2 кнопки в ряду).

    Возвращает:
      - InlineKeyboardMarkup, готовую для отправки пользователю.
    """
    # Создаем билдер для формирования inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопку "◀️Вернутся" для возврата на предыдущий уровень меню.
    # При нажатии callback-данные будут сформированы
    # с уменьшенным уровнем и именем меню 'main'.
    keyboard.add(
        InlineKeyboardButton(
            text="◀️Вернутся",
            callback_data=MenuCallBack(level=level - 1,
                                       menu_name="main").pack(),
        )
    )

    # Добавляем кнопку "Корзина 🛒" для перехода в корзину.
    # Здесь уровень жестко задан равным 3, а имя меню — 'cart'.
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="cart", product_id=42).pack(),
        )
    )

    # Для каждой категории из списка добавляем отдельную кнопку.
    # Текст кнопки — название категории, а callback-данные содержат:
    # - увеличенный уровень меню (level + 1),
    # — имя меню, равное названию категории,
    # — идентификатор категории (category).
    for ctg in categories:
        keyboard.add(
            InlineKeyboardButton(
                text=ctg.name,
                callback_data=MenuCallBack(
                    level=level + 1, menu_name=ctg.name, category=ctg.id
                ).pack(),
            )
        )

    # Распределяем кнопки по рядам согласно переданным размерам.
    # Метод adjust() задает, сколько кнопок будет в каждом ряду.
    return keyboard.adjust(*sizes).as_markup()  # type: ignore
