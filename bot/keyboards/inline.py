from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Определение структуры данных для меню обратного вызова
class MenuCallBack(CallbackData, prefix="menu"):
    level: int  # Уровень вложенности меню
    menu_name: str  # Название текущего меню
    category: int | None = None  # ID категории (если требуется)
    page: int = 1  # Номер страницы меню
    product_id: int | None = None  # ID продукта (если требуется)


# Определение структуры данных для управления действиями по заказу
class OrderCallbackData(CallbackData, prefix="order"):
    action: str  # Действие — например, "create", "confirm" и т.д.
    user_id: int | None = None  # ID пользователя (если требуется)


# Функция для создания основной клавиатуры пользователя
def get_user_main_btn(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    # Определение кнопок и их назначения
    btn = {
        "Товары 🍭|💨": "catalog",
        "Корзина 🛒": "cart",
        "О нас 💬": "about",
        "Оплата 💳": "payment",
        "Доставка 📦": "shipping",
    }
    # Создание кнопок на основе словаря
    for text, menu_name in btn.items():
        if menu_name == 'catalog':  # Обработка кнопки "Каталог"
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level + 1,
                    menu_name=menu_name).pack()
            ))
        elif menu_name == 'cart':  # Обработка кнопки "Корзина"
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=3,
                    menu_name=menu_name).pack()
            ))
        else:  # Для всех остальных кнопок
            keyboard.add(InlineKeyboardButton(
                text=text,
                callback_data=MenuCallBack(
                    level=level,
                    menu_name=menu_name).pack()
            ))
    return keyboard.adjust(*sizes).as_markup()


# Функция для создания клавиатуры раздела каталога
def get_user_catalog_btn(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    # Добавление кнопки "Назад"
    keyboard.add(InlineKeyboardButton(
        text="◀️Вернутся назад",
        callback_data=MenuCallBack(
            level=level - 1,
            menu_name='main').pack()
    ))
    # Добавление кнопки "Корзина"
    keyboard.add(InlineKeyboardButton(
        text="Корзина 🛒",
        callback_data=MenuCallBack(
            level=3,
            menu_name='cart').pack()
    ))

    # Добавление кнопок на основе категорий
    for ctg in categories:
        keyboard.add(InlineKeyboardButton(
            text=ctg.name,
            callback_data=MenuCallBack(
                level=level + 1,
                menu_name=ctg.name,
                category=ctg.id).pack()
        ))
    return keyboard.adjust(*sizes).as_markup()


# Функция для создания клавиатуры продукта
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


# Функция для клавиатуры корзины пользователя
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
            text="Удалить", callback_data=MenuCallBack(
                level=level,
                menu_name='delete',
                product_id=product_id,
                page=page).pack()
        ))
        keyboard.add(InlineKeyboardButton(
            text="-1", callback_data=MenuCallBack(
                level=level,
                menu_name='decrement',
                product_id=product_id,
                page=page).pack()
        ))
        keyboard.add(InlineKeyboardButton(
            text="+1", callback_data=MenuCallBack(
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
                text="Обратно в меню",
                callback_data=MenuCallBack(level=0, menu_name='main').pack()
            ),
            InlineKeyboardButton(
                text="Оформить заказ",
                callback_data=MenuCallBack(level=4, menu_name='checkout').pack()
            ),
        ]
        return keyboard.row(*row_2).as_markup()
    else:
        # Если страница не задана, только кнопка возврата в меню
        keyboard.add(InlineKeyboardButton(
            text="Обратно в меню",
            callback_data=MenuCallBack(
                level=0,
                menu_name='main').pack()
        ))
        return keyboard.adjust(*sizes).as_markup()


# Функция создания клавиатуры для обработки оплаты
def get_payment_keyboard(order_id: int, user_id=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=f"confirm_order_{order_id}"
        ),
        InlineKeyboardButton(
            text="💬 Связаться с клиентом",
            url=f"tg://user?id={user_id}"
        )
    )
    return keyboard.adjust(1).as_markup()

# Универсальная функция для создания произвольной клавиатуры из словаря
def get_callback_btn(*, btn: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btn.items():
        keyboard.add(InlineKeyboardButton(
            text=text,
            callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
