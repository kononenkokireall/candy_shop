from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем запросы ORM для работы с базой данных
from database.orm_querys.orm_query_banner import orm_get_banner

# Импортируем модули для создания клавиатуры
from keyboards.inline_main import get_user_main_btn

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from typing import Tuple, Optional


async def main_menu(
        session: AsyncSession,
        level: int,
        menu_name: str
,       user_id: int) -> Tuple[Optional[InputMediaPhoto], InlineKeyboardMarkup]:
    """
    Создает контент главного меню с баннером и клавиатурой

    Args:
        session: Сессия БД
        level: Текущий уровень меню
        menu_name: Название меню для поиска баннера

    Returns:
        Tuple с медиа-контентом и клавиатурой
        :param session:
        :param level:
        :param menu_name:
        :param user_id:
    """
    # Получаем баннер с проверкой на None
    banner = await orm_get_banner(session, menu_name)

    # Дефолтные значения для случая отсутствия баннера
    media_content = None
    caption = "Добро пожаловать!"

    if banner:
        caption = banner.description if banner.description else caption
        if banner.image:
            media_content = InputMediaPhoto(media=banner.image,
                                            caption=caption)

    # Всегда возвращаем клавиатуру
    return media_content, get_user_main_btn(level=level, user_id=user_id)