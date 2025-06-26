from typing import Optional, Dict, Tuple, List

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
       Клавиатура «карточки товара»:
           ▫ «◀️ Вернуться»  – назад в список категорий
           ▫ «Корзина 🛒»    – сразу в корзину (стр. 1)
           ▫ «Купить 💵»     – положить товар в корзину
           ▫ кнопки пагинации (prev/next)  ─ если переданы

       Args:
           level:     текущий уровень меню.
           category:  id категории (нужен для пагинации).
           page:      номер текущей страницы.
           product_id: id товара.
           pagination_btn: {'⏮️ Назад': 'prev', 'Дальше ⏭️': 'next'}  – любая
                           комбинация; если None - пагинации нет.
           sizes:     схема раскладки главных кнопок (по умолчанию 2 + 1).

       Returns:
           InlineKeyboardMarkup – готовая клавиатура.
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

    keyboard.row(  # «◀️ Вернуться» + «Корзина»
        InlineKeyboardButton(
            text="◀️ Вернуться",
            callback_data=MenuCallBack(level=level - 1,
                                       menu_name="catalog").pack(),
        ),
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3,
                                       menu_name="cart",
                                       page=1).pack(),
        ),
    )
    keyboard.add(  # отдельной строкой – «Купить»
        InlineKeyboardButton(
            text="Купить 💵",
            callback_data=MenuCallBack(level=level,
                                       menu_name="add_to_cart",
                                       product_id=product_id).pack(),
        )
    )

    if pagination_btn:  # None → {}
        row: List[InlineKeyboardButton] = []
        for text, action in pagination_btn.items():
            if action not in {"prev", "next"}:
                # игнорируем неизвестные действия
                continue

            new_page = page + 1 if action == "next" else max(page - 1, 1)
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=level,
                                               menu_name=action,
                                               category=category,
                                               page=new_page).pack(),
                )
            )
        if row:
            keyboard.row(*row)

        # ─────────────────────── финиш ──────────────────────────────────────
    return keyboard.adjust(*sizes).as_markup()
