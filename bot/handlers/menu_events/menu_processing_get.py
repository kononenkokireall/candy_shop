from typing import Optional, Tuple, cast

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.menu_events.menu_main import main_menu

from handlers.menu_events.menu_process_cart import carts

from handlers.menu_events.menu_process_catalog import catalog, products
from handlers.user_events.user_checkout import checkout

from utilit.config import settings

from utilit.notification import NotificationService


# Функция для обработки запросов меню на основе уровня и действия
async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    notification_service: Optional[NotificationService] = None,
    product_id: Optional[int] = None,
    category: Optional[int] = None,
    page: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Tuple[Optional[InputMediaPhoto], Optional[InlineKeyboardMarkup]]:
    # Проверяем уровень меню и вызываем соответствующую функцию
    if level == 0:  # Главная страница
        return await main_menu(session, level, menu_name, user_id)
    elif level == 1:  # Каталог
        return await catalog(session, level, menu_name)
        # Уровень 2: Товары (category и page обязательны)
    elif level == 2:
        if category is None or page is None:
            raise ValueError("Для уровня 2 требуются category и page")
        return await products(
            session=session,
            level=level,
            category=int(category),  # Гарантированно int
            page=int(page)  # Гарантированно int
        )

    # Уровень 3: Корзина (page, user_id, product_id обязательны)
    elif level == 3:
        if page is None or user_id is None or product_id is None:
            raise ValueError(
                "Для уровня 3 требуются page, user_id и product_id")
        return await carts(
            session=session,
            level=level,
            menu_name=menu_name,
            page=int(page),  # Гарантированно int
            user_id=int(user_id),  # Гарантированно int
            product_id=int(product_id)  # Гарантированно int
        )

    # Уровень 4: Оформление заказа (user_id обязателен)
    elif level == 4:
        if user_id is None:
            raise ValueError("Для уровня 4 требуется user_id")
        return await checkout(
            session=session,
            user_id=int(user_id),  # Гарантированно int
            notification_service=notification_service
        )

    else:
        raise ValueError(f"Недопустимый уровень: {level}")