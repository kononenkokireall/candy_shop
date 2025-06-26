import logging
from enum import IntEnum
from typing import Callable, Awaitable

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.menu_events.menu_main import main_menu
from handlers.menu_events.menu_process_cart import carts
from handlers.menu_events.menu_process_catalog import catalog, products

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MenuLevel(IntEnum):
    MAIN = 0
    CATALOG = 1
    PRODUCTS = 2
    CART = 3

MediaResp = tuple[InputMediaPhoto | None, InlineKeyboardMarkup]
Handler = Callable[..., Awaitable[MediaResp]]

# Карта уровней → коро утин-обработчик + перечень обязательных аргументов
MENU_ROUTING: dict[MenuLevel, tuple[Handler, tuple[str, ...]]] = {
    MenuLevel.MAIN: (main_menu, ()),
    MenuLevel.CATALOG: (catalog, ()),
    MenuLevel.PRODUCTS: (products, ("category",)),  # page нормализуем
    MenuLevel.CART: (carts, ("user_id",)),
}


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
) -> MediaResp:
    """Диспетчер: по уровню вызывает нужный генератор меню."""

    try:
        lvl = MenuLevel(level)
    except ValueError:
        raise ValueError(f"Unknown menu level {level}")

    handler, required = MENU_ROUTING[lvl]

    # Грубая валидация обязательных параметров
    missing = {
        "category": category,
        "page": page,
        "user_id": user_id,

    }
    for name in required:
        if missing.get(name) is None:
            raise ValueError(
                f"Parameter «{name}» is required for level {level}")

    # Нормализация
    page = page or 1

    # Вызываем соответствующий коро утин
    if lvl is MenuLevel.MAIN:
        return await handler(session, level, menu_name)
    if lvl is MenuLevel.CATALOG:
        return await handler(session, level, menu_name)
    if lvl is MenuLevel.PRODUCTS:
        return await handler(session, level, category, page)
    if lvl is MenuLevel.CART:
        return await handler(session, level, menu_name, page, user_id,
                             product_id)

    # на всякий случай
    raise RuntimeError("Unreachable code")