# Клавиатуры ReplyKeyboardMarkup для основных действий и InlineKeyboardMarkup
# для уточняющих шагов.
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

# --- Основное меню (ReplyKeyboardMarkup) ---


def main_menu_keyboard():
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

# --- Клавиатура для взаимодействия с товаром и управления корзиной ---


def item_detali_keyboard(category_key: str):
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


def catalog_keyboard():
    """
    Инлайн-клавиатура для выбора категории товаров.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Canabis Lollipops", callback_data="catalog_lollypops")],
            [InlineKeyboardButton(
                text="Акссесуары", callback_data="catalog_accessories")],
        ]
    )
# --- Клавиатура для выбора способа оплаты (InlineKeyboardMarkup) ---


def payment_methods_keyboard():
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


def confirmation_keyboard():
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


def help_keyboard():
    """
    Инлайн-клавиатура для отображения ссылки на поддержку.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="@CBDS_sweet: служба поддержки", url="Ссылка на бота")],
        ]
    )
