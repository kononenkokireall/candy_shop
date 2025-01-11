# Клавиатуры для основных действий пользователя
import logging
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from data.catalog_data import PRODUCT_CATALOG

# Настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Константы для настроек ReplyKeyboardMarkup ---
DEFAULT_REPLY_MARKUP_SETTING = {"resize_keyboard": True}
DEFAULT_ONETIME_REPLY_MARKUP_SETTINGS = {"resize_keyboard": True, "one_time_keyboard": True}


# --- Конфигурация для динамического управления данными ---
CITIES = ["Варшава", "Краков", "Познань", "Вроцлав"]
MAX_CALLOW_LENGTH = 64


# --- Вспомогательная функция для логирования выполнения функции ---
def log_execution(func):
    """Декоратор для логирования выполнения функции."""
    def wrapper(*args, **kwargs):
        logger.info(f"Выполнение функции {func.__name__} с аргументами: {args}, {kwargs}")
        result = func(*args, **kwargs)
        logger.info(f"Завершение выполнения функции {func.__name__}")
        return result
    return wrapper


# --- Вспомогательная функция для сохранения callback_data ---
def short_callback_data(data: str) -> str:
    """Сокращает callback_data, если оно превышает лимит в 64 символа."""
    if len(data) > MAX_CALLOW_LENGTH:
        logger.warning(f"Длина callback_data превышает лимит: {data}")
    return data[:MAX_CALLOW_LENGTH]


# --- Вспомогательная функция для создания InlineKeyboardMarkup ---\
@log_execution
def create_inline_keyboard(buttons: list):
    """
    Создает InlineKeyboardMarkup из списка кнопок.
    Параметры:
    - buttons: список списков с InlineKeyboardButton.
    Возвращает:
    - InlineKeyboardMarkup объект.
    """
    return InlineKeyboardMarkup(inline_keyboard=buttons)



# --- Клавиатура для выбора города ---
@log_execution
def create_city_selection_keyboard():
    """Клавиатура для выбора города"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=city, callback_data=f"city:{city}") for city in CITIES],
        ],
        **DEFAULT_ONETIME_REPLY_MARKUP_SETTINGS
    )


# --- Основное меню (ReplyKeyboardMarkup) ---
@log_execution
def create_main_menu_keyboard():
    """Клавиатура основного меню."""
    return ReplyKeyboardMarkup(
        inline_keyboard=[
            [KeyboardButton(text="Каталог товаров", callback_data="catalog_main")],
            [KeyboardButton(text="Ваша Корзина", callback_data="cart_main")],
            [KeyboardButton(text="Помощь", callback_data="help_main")],
            [KeyboardButton(text="Изменить город", callback_data="city_selection")]
        ],
        **DEFAULT_REPLY_MARKUP_SETTING
    )


# --- Каталог товаров (InlineKeyboardMarkup) ---
@log_execution
def create_catalog_keyboard(categories: list):
    """Динамическая клавиатура для выбора категории товаров."""
    return create_inline_keyboard([
            [InlineKeyboardButton(
                text=category['category_name'],
                callback_data=short_callback_data(f"catalog_{category['key']}")
            )] for category in categories
        ])


# --- Клавиатура для взаимодействия с товаром и управления корзиной ---
@log_execution
def create_item_detail_keyboard(category_key: str):
    """Клавиатура для взаимодействия с товаром"""
    return create_inline_keyboard([
            [InlineKeyboardButton(text="Добавить в корзину",
            callback_data=f"add_to_cart_{category_key}")],

            [InlineKeyboardButton(text="Вернутся в каталог",
            callback_data="catalog_return")],

            [InlineKeyboardButton(text="Очистить корзину",
            callback_data="cart_clear")],

            [InlineKeyboardButton(text="Оформить заказ",
            callback_data="cart_checkout")],
        ])


# --- Клавиатура для выбора способа оплаты (InlineKeyboardMarkup) ---
@log_execution
def create_payment_methods_keyboard():
    """Клавиатура для способа оплаты"""
    return create_inline_keyboard([
            [InlineKeyboardButton(text="Карта",
                                  callback_data=short_callback_data("payment-card"))],
            [InlineKeyboardButton(text="Наличные",
                                  callback_data=short_callback_data("payment-cash"))],
        ])


# --- Подтверждение Заказа(ReplyKeyboardMarkup) ---
@log_execution
def create_confirmation_keyboard():
    """Клавиатура для подтверждения оплаты"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить")],
            [KeyboardButton(text="Отменить")],
        ],
        **DEFAULT_ONETIME_REPLY_MARKUP_SETTINGS
    )


# --- Клавиатура со ссылкой на поддержку ---
@log_execution
def create_help_keyboard():
    """Клавиатура для отображения ссылки на поддержку."""
    support_url = "@CBDS_sweet"
    if not support_url.startswith("@@CBDS_sweet") and not support_url.startswith("@CBDS_sweet"):
        logger.error(f"Некорректный URL для поддержки: {support_url}")
        raise ValueError(f"Некорректный URL: {support_url}")

    return create_inline_keyboard([
            [InlineKeyboardButton(
                text="Служба поддержки", url=support_url)],
        ])
