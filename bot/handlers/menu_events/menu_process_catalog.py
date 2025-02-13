from aiogram.types import InputMediaPhoto

from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_product import orm_get_products
from handlers.menu_events.menu_paginator_navi import pages
from keyboards.inline_catalog import get_user_catalog_btn
from keyboards.inline_product import get_user_product_btn
from utilit.paginator import Paginator


# Функция для формирования меню каталога (уровень 1)
async def catalog(session, level, menu_name):
    # Получаем баннер для каталога
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    # Загружаем список категорий из базы данных
    categories = await orm_get_categories(session)
    # Генерируем клавиатуру для категорий
    keyboards = get_user_catalog_btn(level=level, categories=categories)
    return image, keyboards


# Функция для отображения товаров из каталога (уровень 2)
async def products(session, level, category, page):
    # Получаем список товаров из категории
    products_user = await orm_get_products(session, category_id=category)
    paginator = Paginator(products_user, page=page)
    product_user = paginator.get_page()[0]  # Берем первый товар на текущей странице
    # Создаем медиа-объект для продукта
    image = InputMediaPhoto(
        media=product_user.image,
        caption=f"<strong>{product_user.name}</strong>\n{product_user.description}\n"
                f"Стоимость: {round(product_user.price, 2)} PLN.\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )
    # Создаем кнопки навигации для пагинации
    pagination_btn = pages(paginator)
    keyboards = get_user_product_btn(
        level=level,
        category=category,
        page=page,
        pagination_btn=pagination_btn,
        product_id=product_user.id,
    )
    return image, keyboards
