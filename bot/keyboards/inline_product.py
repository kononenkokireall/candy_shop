# Функция для создания клавиатуры продукта
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack

# Функция для создания клавиатуры покупки продукта
def get_user_product_btn(
        *,
        level: int,
        category: int,
        page: int,
        pagination_btn: dict,
        product_id: int,
        sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()
    # Кнопка "Назад"
    keyboard.add(InlineKeyboardButton(
        text="◀️Вернутся назад",
        callback_data=MenuCallBack(
            level=level - 1,
            menu_name='catalog').pack()
    ))
    # Кнопка "Корзина"
    keyboard.add(InlineKeyboardButton(
        text="Корзина 🛒",
        callback_data=MenuCallBack(
            level=3,
            menu_name='cart').pack()
    ))
    # Кнопка "Купить"
    keyboard.add(InlineKeyboardButton(
        text="Купить 💵",
        callback_data=MenuCallBack(
            level=level, menu_name='add_to_cart',
            product_id=product_id).pack()
    ))
    keyboard.adjust(*sizes)

    # Постраничная навигация (pagination)
    row = []
    for text, menu_name in pagination_btn.items():
        if menu_name == 'next':  # Кнопка "Вперед"
            row.append(InlineKeyboardButton(
                text=text, callback_data=MenuCallBack(
                    level=level,
                    menu_name=menu_name,
                    category=category,
                    page=page + 1).pack()
            ))
        elif menu_name == 'prev':  # Кнопка "Назад"
            row.append(InlineKeyboardButton(
                text=text, callback_data=MenuCallBack(
                    level=level,
                    menu_name=menu_name,
                    category=category,
                    page=page - 1).pack()
            ))
    return keyboard.row(*row).as_markup()
