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
# --- Католог товаров (InlineKeyboardMarkup) ---


def catalog_keyboard():
    """
    Инлайн-клавиатура для выбора категории товаров.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Шоколад", callback_data="catalog_chocolate")],
            [InlineKeyboardButton(
                text="Леденцы", callback_data="catalog_candies")],
            [InlineKeyboardButton(
                text="Карамель", callback_data="catalog_caramel")],
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
