from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto

from database.orm_query import (
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    Paginator)

from keyboards.inline import (
    get_user_main_btn,
    get_user_catalog_btn,
    get_user_product_btn)


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    keyboards = get_user_main_btn(level=level)
    return image, keyboards


async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    categories = await orm_get_categories(session)
    keyboards = get_user_catalog_btn(level=level, categories=categories)
    return image, keyboards


def pages(paginator: Paginator):
    btn = dict()
    if paginator.has_previous():
        btn["◀️Пред."] = "prev"
    if paginator.has_next():
        btn["След.▶️"] = "next"
    return btn



async def products(session, level, category, page):
    products_user = await orm_get_products(session, category_id=category)
    paginator = Paginator(products_user, page=page)
    product_user = paginator.get_page()[0]
    image = InputMediaPhoto(
        media=product_user.image,
        caption=f"<strong>{product_user.name}</strong>\n{product_user.description}\n"
                f"Стоимость: {round(product_user.price, 2)}\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btn = pages(paginator)
    keyboards = get_user_product_btn(
        level=level,
        category=category,
        page=page,
        pagination_btn=pagination_btn,
        product_id=product_user.id,
    )

    return image, keyboards

async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await products(session, level, category, page)