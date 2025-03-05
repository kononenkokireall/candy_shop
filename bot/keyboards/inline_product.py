from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


def get_user_product_btn(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btn: dict | None = None,  # Разрешаем None
        product_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    # Добавляем основные кнопки
    keyboard.add(
        InlineKeyboardButton(
            text="◀️Вернутся",
            callback_data=MenuCallBack(level=level - 1, menu_name="catalog").pack()
        ),
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="cart").pack()
        ),
        InlineKeyboardButton(
            text="Купить 💵",
            callback_data=MenuCallBack(
                level=level, menu_name="add_to_cart", product_id=product_id).pack()
        )
    )

    # Настраиваем расположение кнопок
    keyboard.adjust(*sizes)

    # Обрабатываем пагинацию
    pagination_btn = pagination_btn or {}  # Заменяем None на пустой словарь
    pagination_row = []

    for text, action in pagination_btn.items():
        if action == "next":
            new_page = page + 1
        elif action == "prev":
            new_page = page - 1
        else:
            continue

        pagination_row.append(
            InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level,
                    menu_name=action,
                    category=category,
                    page=new_page
                ).pack()
            )
        )

    # Добавляем пагинацию, только если есть кнопки
    if pagination_row:
        keyboard.row(*pagination_row)

    return keyboard.as_markup()