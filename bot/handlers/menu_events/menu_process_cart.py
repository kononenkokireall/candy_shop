from aiogram.types import InputMediaPhoto

from database.orm_querys_order.orm_query_create_order import (
    orm_delete_from_cart,
    orm_reduce_product_in_cart,
    orm_add_to_cart,
    orm_get_user_carts,
    orm_get_banner
)

from handlers.menu_events.menu_paginator_navi import pages
from keyboards.inline_cart import get_user_cart_btn
from utilit.paginator import Paginator


# Функция для управления корзиной (уровень 3)
async def carts(session, level, menu_name, page, user_id, product_id):
    # Обработка действий в корзине
    if menu_name == 'delete':  # Удаление товара из корзины
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1: page -= 1  # Проверяем текущую страницу
    elif menu_name == 'decrement':  # Уменьшение количества товара
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart: page -= 1
    elif menu_name == 'increment':  # Увеличение количества товара
        await orm_add_to_cart(session, user_id, product_id)

    # Получаем содержимое корзины пользователя
    carts_user = await orm_get_user_carts(session, user_id)

    if not carts_user:  # Если корзина пуста, показываем баннер
        banner = await orm_get_banner(session, 'cart')
        image = InputMediaPhoto(media=banner.image, caption=f"<strong>{banner.description}</strong>")
        keyboards = get_user_cart_btn(
            level=level,
            page=None,
            pagination_btn=None,
            product_id=None,
        )
    else:
        # Если в корзине есть товары, используем paginator
        paginator = Paginator(carts_user, page=page)
        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(sum(cart.quantity * cart.product.price for cart in carts_user), 2)
        # Отображаем информацию о текущем товаре из корзины и общую сумму
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n"
                    f"{cart.product.price}.PLN x {cart.quantity} = {cart_price}.PLN\n"
                    f"Товар {paginator.page} из {paginator.pages} в корзине.\n"
                    f"Общая сумма товаров в корзине: {total_price}.PLN",
        )

        # Генерируем кнопки для управления корзиной (навигатор)
        pagination_btn = pages(paginator)
        keyboards = get_user_cart_btn(
            level=level,
            page=page,
            pagination_btn=pagination_btn,
            product_id=cart.product.id,
        )
    return image, keyboards
