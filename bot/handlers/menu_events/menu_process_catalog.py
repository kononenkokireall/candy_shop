from typing import Tuple, Optional

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner, Category, Product
from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_product import orm_get_products
from handlers.menu_events.menu_paginator_navi import pages
from keyboards.inline_catalog import get_user_catalog_btn
from keyboards.inline_product import get_user_product_btn
from utilit.paginator import Paginator


# Функция для формирования меню каталога (уровень 1)
async def catalog(
        session: AsyncSession,
        level: int,
        menu_name: str
) -> Tuple[Optional[InputMediaPhoto], InlineKeyboardMarkup]:
    # Получаем баннер для каталога

    banner: Optional[Banner] = await orm_get_banner(session, menu_name)
    media = None

    if banner:
        media = InputMediaPhoto(
            media=banner.image,
            caption=banner.description
        )

    # Получаем категории
    raw_categories = await orm_get_categories(session)
    categories_list: list[Category] = list(raw_categories)

    # Генерируем клавиатуру
    keyboard = get_user_catalog_btn(
        level=level,
        categories=categories_list  # Предполагается что принимает list[Category]
    )

    return media, keyboard


# Функция для отображения товаров из каталога (уровень 2)
async def products(
        session: AsyncSession,
        level: int,
        category: int,
        page: int
) -> Tuple[Optional[InputMediaPhoto], InlineKeyboardMarkup]:
    # Получаем товары и преобразуем в list
    raw_products = await orm_get_products(session, category_id=category)
    products_list: list[Product] = list(raw_products)

    # Проверка на пустой список
    if not products_list:
        return None, get_empty_product_keyboard()

    # Инициализируем пагинатор
    paginator = Paginator(products_list, page=page)
    page_items = paginator.get_page()

    # Проверка на пустую страницу
    if not page_items:
        return None, get_empty_page_keyboard()

    product = page_items[0]
    media = InputMediaPhoto(
        media=product.image,
        caption=(
            f"<strong>{product.name}</strong>\n"
            f"{product.description}\n"
            f"Стоимость: {round(product.price, 2)} PLN\n"
            f"Товар {paginator.page} из {paginator.pages}"
        )
    )

    # Кнопки пагинации
    pagination_btn = pages(paginator) or {}

    keyboard = get_user_product_btn(
        level=level,
        category=category,
        page=page,
        pagination_btn=pagination_btn,
        product_id=product.id
    )

    return media, keyboard


def get_empty_page_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для пустой страницы"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Вернуться",
        callback_data="back"
    ))
    return builder.as_markup()


def get_empty_product_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для пустой категории"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Каталог",
        callback_data="catalog"
    ))
    return builder.as_markup()
