from enum import StrEnum
from typing import Tuple, Optional, Callable, Awaitable
import logging
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Cart, Banner
from database.orm_querys.orm_query_banner import orm_get_banner
from database.orm_querys.orm_query_cart import (
    orm_reduce_product_in_cart,
    orm_get_user_carts,
    orm_full_remove_from_cart,
    orm_add_product_to_cart,
)
from handlers.menu_events.menu_paginator_navi import pages
from keyboards.inline_cart import get_user_cart_btn
from keyboards.inline_main import MenuCallBack
from utilit.paginator import Paginator


class CartAction(StrEnum):  # 👈  вставить
    DELETE = "delete"
    DECREMENT = "decrement"
    INCREMENT = "increment"


# Какая кнопка → какой ORM-handler вызываем
ACTIONS: dict[
    CartAction, Callable[[AsyncSession, int, int], Awaitable[bool | None]]] = {
    CartAction.DELETE: orm_full_remove_from_cart,
    CartAction.DECREMENT: orm_reduce_product_in_cart,
    CartAction.INCREMENT: orm_add_product_to_cart,
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Функция для управления корзиной (уровень 3)
async def carts(
        session: AsyncSession,
        level: int,
        menu_name: str,
        page: int | None,
        user_id: int,
        product_id: int | None = None,
) -> Tuple[Optional[InputMediaPhoto], InlineKeyboardMarkup]:
    """
    Управление корзиной пользователя с пагинацией

    Args:
        session: Асинхронная сессия БД
        level: Уровень меню
        menu_name: Название действия (delete, decrement, increment)
        page: Текущая страница
        user_id: ID пользователя
        product_id: ID продукта

    Returns:
        Медиа-контент и клавиатура
    """
    # Обработка действий с корзиной
    page = max(page or 1, 1)  # нормализуем сразу

    # ─── 1. выполняем действие, если оно есть ─────────────────────────────
    try:
        action = CartAction(menu_name)  # пытаемся интерпретировать строку
    except ValueError:
        action = None  # это просто просмотр без изменений
    try:
        if action and product_id:
            handler = ACTIONS[action]
            item_exists = await handler(session, user_id, product_id) or False

            if page > 1 and not item_exists:
                page -= 1


            # Получаем содержимое корзины и преобразуем в list
            raw_carts = await orm_get_user_carts(session, user_id)
            if raw_carts is None:
                raw_carts = []

            carts_user: list[Cart] = list(raw_carts)

            if not carts_user:
                banner: Optional[Banner] = await orm_get_banner(session, "cart")
                media = None
                if banner:
                    media = InputMediaPhoto(
                        media=banner.image,
                        caption=f"<strong>{banner.description}</strong>"
                    )
                keyboard = get_user_cart_btn(
                    level=level,
                    page=None,
                    pagination_btn=None,
                    product_id=None
                )
                return media, keyboard

            # Инициализируем пагинатор с list
            paginator = Paginator(carts_user, page=page)
            page_items = paginator.get_page()

            if not page_items:
                return None, get_empty_cart_keyboard()

            cart = page_items[0]
            cart_price = round(cart.quantity * cart.product.price, 2)
            total_price = round(
                sum(item.quantity * item.product.price for item in carts_user), 2
            )

            media = InputMediaPhoto(
                media=cart.product.image,
                caption=(
                    f"<strong>{cart.product.name}</strong>\n"
                    f"{cart.product.price} PLN x {cart.quantity} = {cart_price} PLN\n"
                    f"Товар {paginator.page} из {paginator.pages}\n"
                    f"Общая сумма: {total_price} PLN"
                )
            )

            pagination_btn = pages(paginator) or {}
            keyboard = get_user_cart_btn(
                level=level,
                page=page,
                pagination_btn=pagination_btn,
                product_id=cart.product.id
            )

            return media, keyboard
    except Exception as e:
        logger.exception("Ошибка в carts(): %s", e)
    banner = await orm_get_banner(session, "error")  # если хотите
    media = (
        InputMediaPhoto(
            media=banner.image,
            caption=banner.description
        )
        if banner else None
    )
    return media, get_empty_cart_keyboard()


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустой корзины"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🛒 В каталог",
        callback_data=MenuCallBack(level=1, menu_name="catalog").pack()
    ))
    return builder.as_markup()
