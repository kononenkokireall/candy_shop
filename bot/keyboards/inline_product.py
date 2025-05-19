from typing import Optional, Dict, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для построения inline-клавиатуры для работы с товарами пользователя.
def get_user_product_btn(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btn: Optional[Dict[str, str]] = None,
        product_id: int,
        sizes: Tuple[int, ...] = (2, 1),
) -> InlineKeyboardMarkup:
    """
    Функция для построения inline-клавиатуры для работы с товарами пользователя.

    Параметры:
    - level: Текущий уровень меню (исп. Для формирования callback-данных).
    - category: Идентификатор категории, к которой относится товар.
    - page: Текущая страница для пагинации.
    - pagination_btn: Словарь, определяющий кнопки пагинации.
     Ключ — текст кнопки, значение — действие ('next' или 'prev').
                      Если не указан, используется пустой словарь.
    - product_id: Идентификатор товара,
     который будет использоваться при оформлении покупки.
    - sizes: Кортеж, определяющий компоновку основных кнопок
     (например, (2, 1) означает два ряда: в первом ряду по 2 кнопки,
      во втором — 1).

    Возвращает:
    - Разметку inline-клавиатуры,
     сформированную с использованием InlineKeyboardBuilder.
    """
    # Создаем билдер для inline-клавиатуры
    keyboard = InlineKeyboardBuilder()

    # Добавляем основные кнопки:
    # 1. "◀️Вернутся" — кнопка для возврата на предыдущий уровень меню
    # (уровень уменьшается на 1)
    # 2. "Корзина 🛒" — кнопка для перехода в корзину
    # (фиксированный уровень 3 и имя меню "cart")
    # 3. "Купить 💵" — кнопка для добавления товара в корзину
    # (используется переданный product_id)
    keyboard.add(
        InlineKeyboardButton(
            text="◀️Вернуться",
            callback_data=MenuCallBack(level=level - 1,
                                       menu_name="catalog").pack(),
        ),
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="cart", page=1,
                                       ).pack(),
        ),
        InlineKeyboardButton(
            text="Купить 💵",
            callback_data=MenuCallBack(
                level=level, menu_name="add_to_cart", product_id=product_id
            ).pack(),
        ),
    )

    # Настраиваем расположение основных
    # кнопок согласно переданным размерам (sizes).
    # Метод adjust распределяет кнопки
    # по рядам в соответствии с заданной компоновкой.
    keyboard.adjust(*sizes)

    # Обрабатываем кнопки пагинации.
    # Если pagination_btn равен None, заменяем его на пустой словарь.
    pagination_btn = pagination_btn or {}
    pagination_row = []  # Список для хранения кнопок пагинации

    # Перебираем пары (текст, действие) из словаря пагинации
    for text, action in pagination_btn.items():
        # Если действие 'next', увеличиваем номер страницы на 1
        if action == "next":
            new_page = page + 1
        # Если действие 'prev', уменьшаем номер страницы на 1
        elif action == "prev":
            new_page = page - 1
        else:
            # Если действие не соответствует 'next' или 'prev',
            # пропускаем данную кнопку
            continue

        # Формируем кнопку пагинации с переданным текстом и callback-данными,
        # включающими текущий уровень,
        # действие, категорию и новый номер страницы
        pagination_row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level, menu_name=action, category=category,
                    page=new_page
                ).pack(),
            )
        )

    # Если сформированы кнопки пагинации,
    # добавляем их в отдельный ряд клавиатуры
    if pagination_row:
        keyboard.row(*pagination_row)

    # Возвращаем итоговую разметку клавиатуры
    return keyboard.as_markup()
