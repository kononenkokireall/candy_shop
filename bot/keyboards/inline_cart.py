from typing import Optional, Dict

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_main import MenuCallBack


# Функция для создания клавиатуры корзины пользователя.
def get_user_cart_btn(
        *,
        # Текущий уровень меню (используется для формирования callback-данных)
        level: int,
        # Номер страницы корзины; если задан,
        # значит корзина содержит список товаров с постраничной навигацией
        page: Optional[int],
        # Словарь кнопок пагинации (например, {"Вперед": "next",
        # "Назад": "prev"})
        pagination_btn: Optional[Dict[str, str]],
        # Идентификатор продукта,
        # для которого выполняется действие (может быть None)
        product_id: Optional[int],
        # Кортеж, определяющий компоновку кнопок в ряды (например, (3,)
        # означает 3 кнопки в ряду)
        sizes: tuple[int, ...] = (3,)
) -> InlineKeyboardMarkup:
    # Создаем билдер для формирования inline-клавиатуры.
    keyboard = InlineKeyboardBuilder()

    # Если параметр page задан (т.е. Корзина содержит постраничную навигацию)
    if page:
        # Добавляем кнопку "❌ Удалить" для удаления продукта из корзины.
        # Callback-данные включают текущий уровень, действие 'delete',
        # product_id и номер страницы.
        keyboard.add(
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=MenuCallBack(
                    level=level,
                    menu_name="delete",
                    product_id=product_id,
                ).pack(),
            )
        )
        # Добавляем кнопку "➖" для уменьшения количества товара.
        keyboard.add(
            InlineKeyboardButton(
                text="➖",
                callback_data=MenuCallBack(
                    level=level, menu_name="decrement", product_id=product_id,
                    page=page
                ).pack(),
            )
        )
        # Добавляем кнопку "➕" для увеличения количества товара.
        keyboard.add(
            InlineKeyboardButton(
                text="➕",
                callback_data=MenuCallBack(
                    level=level, menu_name="increment", product_id=product_id,
                    page=page
                ).pack(),
            )
        )

        # Распределяем добавленные кнопки по рядам согласно заданным размерам.
        keyboard.adjust(*sizes)

        # Обработка кнопок для постраничной навигации.
        # Если передан словарь пагинации,
        # формируем отдельный ряд с кнопками "next" и "prev".
        if pagination_btn:  # Проверяем, что pagination_btn не None и не пустой
            row = []  # Инициализируем список для кнопок пагинации
            for text, menu_name in pagination_btn.items():
                if menu_name == "next":
                    row.append(
                        InlineKeyboardButton(
                            text=text,
                            callback_data=MenuCallBack(
                                level=level,
                                menu_name=menu_name,
                                page=page + 1
                            ).pack()
                        )
                    )
                elif menu_name == "prev":
                    row.append(
                        InlineKeyboardButton(
                            text=text,
                            callback_data=MenuCallBack(
                                level=level,
                                menu_name=menu_name,
                                page=page - 1
                            ).pack()
                        )
                    )

            # Добавляем ряд только если есть кнопки
            if row:
                keyboard.row(*row)

        # Формируем дополнительный ряд с действиями:
        # 1. Кнопка "🏠Меню" для возврата в главное меню
        # (уровень 0, меню 'main')
        # 2. Кнопка "Оформление 🚀" для перехода к оформлению заказа
        # (фиксированный уровень 4, меню 'checkout')
        row_2 = [
            InlineKeyboardButton(
                text="🏠Меню",
                callback_data=MenuCallBack(level=0, menu_name="main")
                .pack(),
            ),
            InlineKeyboardButton(
                text="Оформление 🚀",
                callback_data=MenuCallBack(level=4, menu_name="checkout")
                .pack(),
            ),
        ]
        keyboard.row(*row_2)
        return keyboard.as_markup()

        # Добавляем этот дополнительный ряд и возвращаем итоговую клавиатуру.
    else:
        # Если параметр page не задан,
        # значит корзина не использует постраничную навигацию.
        # В этом случае добавляем только кнопку для возврата в главное меню.
        keyboard.add(
            InlineKeyboardButton(
                text="🏠Обратно в меню",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            )
        )
        # Возвращаем клавиатуру
        # с настройкой расположения кнопок согласно sizes.
        keyboard.adjust(*sizes)

        return keyboard.as_markup()
