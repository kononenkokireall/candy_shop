from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto

from database.orm_query import (
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    Paginator, orm_delete_from_cart, orm_reduce_product_in_cart, orm_add_to_cart, orm_get_user_carts)

from keyboards.inline import (
    get_user_main_btn,
    get_user_catalog_btn,
    get_user_product_btn, get_user_cart_btn)


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


async def carts(session, level, menu_name, page, user_id, product_id):
    if menu_name == 'delete':
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1: page -=1
    elif menu_name == 'decrement':
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart: page -=1
    elif menu_name == 'increment':
        await orm_add_to_cart(session, user_id, product_id)

    carts_user = await orm_get_user_carts(session, user_id)

    if not carts_user:
        banner = await orm_get_banner(session, 'cart')
        image = InputMediaPhoto(media=banner.image, caption=f"<strong>{banner.description}</strong>")
        keyboards = get_user_cart_btn(
            level=level,
            page=None,
            pagination_btn=None,
            product_id=None,
        )
    else:
        paginator = Paginator(carts_user, page=page)
        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(sum(cart.quantity * cart.product.price for cart in carts_user), 2)
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n"
                    f"{cart.product.price}.PLN x {cart.quantity} = {cart_price}.PLN\n"
                    f"Товар {paginator.page} из {paginator.pages} в корзине.\n"
                    f"Общая сумма товаров в корзине: {total_price}.PLN",
        )

        pagination_btn = pages(paginator)
        keyboards = get_user_cart_btn(
            level=level,
            page=page,
            pagination_btn=pagination_btn,
            product_id=cart.product.id,
        )
        return image, keyboards


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        product_id: int | None = None,
        category: int | None = None,
        page: int | None = None,
        user_id: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await products(session, level, category, page)
    elif level == 3:
        return await carts(session, level, menu_name, page, user_id, product_id)