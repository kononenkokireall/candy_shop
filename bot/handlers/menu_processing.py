from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto
from database.orm_query import orm_get_banner, orm_get_categories
from keyboards.inline import get_user_main_btn, get_user_catalog_btn


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


async def get_menu_content(session: AsyncSession, level: int, menu_name: str):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)