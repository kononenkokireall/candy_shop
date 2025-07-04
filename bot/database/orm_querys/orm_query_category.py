import logging
from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from cache.decorators import cached
from cache.invalidator import CacheInvalidator

from ..models import Category

logger = logging.getLogger(__name__)


@cached("categories:all", ttl=3600, model=Category)
async def orm_get_categories(session: AsyncSession) -> Sequence[Category]:
    """
    Получить все категории товаров с кэшированием.
    Используется @cached-декоратор для авто-кэширования и десериализации.
    """
    logger.info("Запрос всех категорий товаров")
    try:
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        return categories
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {str(e)}")
        raise


async def orm_create_categories(session: AsyncSession,
                                categories: List[str]) -> int:
    """
    Создать новые категории, если их ещё нет в базе.
    Инвалидирует кэш после добавления.
    """
    if not categories:
        logger.warning("Попытка добавления пустого списка категорий")
        return 0

    logger.info(f"Начало обработки {len(categories)} категорий")
    try:
        existing = await session.execute(
            select(Category.name).where(Category.name.in_(categories))
        )
        existing_names = {name for name in existing.scalars()}

        new_categories = [
            Category(name=name) for name in categories
            if name not in existing_names
        ]

        if not new_categories:
            logger.info("Все категории уже существуют в базе")
            return 0

        session.add_all(new_categories)
        #await session.commit()
        await CacheInvalidator.invalidate_by_pattern("categories*")
        logger.info(f"Успешно добавлено {len(new_categories)} новых категорий")
        return len(new_categories)

    except Exception as e:
       # await session.rollback()
        logger.critical(
            f"Критическая ошибка при добавлении категорий: {str(e)}")
        raise
