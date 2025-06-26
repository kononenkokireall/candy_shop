from typing import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для создания клавиатуры раздела каталога.
def get_user_catalog_btn(
        *,
        level: int,
        categories: Sequence,
        row_sizes: Sequence[int] = (2,),
        cart_level: int = 3, ) -> InlineKeyboardMarkup:
    """
      Клавиатура каталога.

      :param level: Текущий уровень меню
      :param categories: итерируемый со свойствами ``id`` и ``name``
      :param row_sizes: схема строк для категорий (по умолчанию 2 в ряд)
      :param cart_level: level, на который ведёт кнопка «Корзина»
      """
    # Создаем билдер для формирования inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # --- системные кнопки -------------------------------------------------
    keyboard.row(
        InlineKeyboardButton(
            text="◀️ Вернуться",
            callback_data=MenuCallBack(
                level=max(level - 1, 0), menu_name="main"
            ).pack(),
        ),
        InlineKeyboardButton(
            text="🛒 Корзина",
            callback_data=MenuCallBack(
                level=cart_level, menu_name="cart", page=1
            ).pack(),
        ),
    )

    # --- категории --------------------------------------------------------
    for ctg in categories:
        keyboard.button(
            text=ctg.name,
            callback_data=MenuCallBack(
                level=level + 1,
                menu_name="category",  # фиксированное имя
                category=ctg.id,
                page=1
            ).pack(),
        )

    keyboard.adjust(*row_sizes)
    return keyboard.as_markup()
