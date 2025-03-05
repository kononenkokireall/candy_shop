# Функция для клавиатуры корзины пользователя
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для создания клавиатуры корзины
def get_user_cart_btn(
        *,
        level: int,
        page: int | None,
        pagination_btn: dict | None,
        product_id: int | None,
        sizes: tuple[int] = (3,)
):
    keyboard = InlineKeyboardBuilder()
    if page:  # Если номер страницы задан
        # Кнопки для управления продуктами (удаление, увеличение/уменьшение количества)
        keyboard.add(InlineKeyboardButton(
            text="❌ Удалить", callback_data=MenuCallBack(
                level=level,
                menu_name='delete',
                product_id=product_id,
                page=page).pack()
        ))
        keyboard.add(InlineKeyboardButton(
            text="➖", callback_data=MenuCallBack(
                level=level,
                menu_name='decrement',
                product_id=product_id,
                page=page).pack()
        ))
        keyboard.add(InlineKeyboardButton(
            text="➕", callback_data=MenuCallBack(
                level=level,
                menu_name='increment',
                product_id=product_id,
                page=page).pack()
        ))

        keyboard.adjust(*sizes)

        # Постраничная навигация
        row = []
        for text, menu_name in pagination_btn.items():
            if menu_name == 'next':
                row.append(InlineKeyboardButton(
                    text=text, callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        page=page + 1).pack()
                ))
            elif menu_name == 'prev':
                row.append(InlineKeyboardButton(
                    text=text, callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        page=page - 1).pack()

                ))
        keyboard.row(*row)

        # Дополнительные действия (оформление заказа, возврат в меню)
        row_2 = [
            InlineKeyboardButton(
                text="🏠Меню",
                callback_data=MenuCallBack(level=0, menu_name='main').pack()
            ),
            InlineKeyboardButton(
                text="Оформление 🚀",
                callback_data=MenuCallBack(level=4, menu_name='checkout').pack()
            ),
        ]
        return keyboard.row(*row_2).as_markup()
    else:
        # Если страница не задана, только кнопка возврата в меню
        keyboard.add(InlineKeyboardButton(
            text="🏠Обратно в меню",
            callback_data=MenuCallBack(
                level=0,
                menu_name='main').pack()
        ))
        return keyboard.adjust(*sizes).as_markup()
