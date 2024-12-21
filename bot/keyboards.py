# Клавиатуры ReplyKeyboardMarkup для основных действий и InlineKeyboardMarkup
# для уточняющих шагов.
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

# --- Основное меню (ReplyKeyboardMarkup) ---


def main_menu_kb():
    """
    Клавиатура основного меню для приветствия пользователю и выбора 
    основного действия.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог товаров")],
            [KeyboardButton(text="Ваша Корзина"),
             KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True
    )

# --- Клавиатура для выбора города ---


def city_select_kb():
    """
    Клавиатура для выбора города
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Варшава"), KeyboardButton(text="Краков")],
            [KeyboardButton(text="Вроцлав"), KeyboardButton(text="Познань")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# --- Клавиатура для взаимодействия с товаром и управления корзиной ---


def item_detail_kb(category_key: str):
    """
    Создает инлайн-клавиатуру для взаимодействия с товаром
    Параметры:
    - category_key - ключ категории товара
    Return:
    - InlineKeyboardMarkup с кнопками для добавления товара в корзину и 
    возврата в каталог.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить в корзину",
                                  callback_data=f"add_to_cart_{category_key}")],
            [InlineKeyboardButton(text="Вернутся в каталог",
                                  callback_data="catalog_return")],
            [InlineKeyboardButton(text="Очистить корзину",
                                  callback_data="cart_clear")],
            [InlineKeyboardButton(text="Оформить заказ",
                                  callback_data="cart_checkout")],
        ]
    )

# --- Католог товаров (InlineKeyboardMarkup) ---


def catalog_kb(categories: list):
    """
    Динамическая Инлайн-клавиатура для выбора категории товаров.
    Параметры:
    - сategories - список словарей с полями name и key
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=category['name'], callback_data=f"catalog_{category['key']}")
             ] for category in categories
        ]
    )
# --- Клавиатура для выбора способа оплаты (InlineKeyboardMarkup) ---


def pay_methods_kb():
    """
    Инлайн-клавиатура для способа оплаты
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Карта", callback_data="payment-card")],
            [InlineKeyboardButton(
                text="Наличные", callback_data="payment-cash")],
        ]
    )
# --- Подтверждение Заказа(ReplyKeyboardMarkup) ---


def confi_kb():
    """
    Клавиатура для подтверждения оплаты
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить"),
             KeyboardButton(text="Отменить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
# --- Клавиатура с ссылкой на поддержку (InlineKeyboardMarkup) ---


def help_kb():
    """
    Инлайн-клавиатура для отображения ссылки на поддержку.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="@CBDS_sweet: служба поддержки", url="Ссылка на бота")],
        ]
    )
