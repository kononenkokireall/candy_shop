from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import logging

from cache.decorators import cached
from cache.invalidator import CacheInvalidator
from ..models import Category
from cache.redis import redis_cache  # Подключаем кэширование через Redis

logger = logging.getLogger(__name__)
CATEGORY_TTL = 86400  # 24 часа в секундах


def dict_to_category(data: dict) -> Category:
    """Преобразует словарь в объект Category"""
    return Category(
        id=data["id"],
        name=data["name"],
        created_at=data["created_at"],
        created=data.get("created"),
        updated=data.get("updated")
    )


@cached("categories_all", ttl=CATEGORY_TTL)
async def orm_get_categories(session: AsyncSession) -> Sequence[Category]:
    logger.info("Запрос всех категорий товаров")
    try:
        async with redis_cache.session() as redis:
            cached_data = await redis.get("categories_all")
            if cached_data:
                logger.info("Загрузка категорий из кэша")
                return [dict_to_category(cat) for cat in
                        json.loads(cached_data)]

        result = await session.execute(select(Category))
        categories = result.scalars().all()
        serialized_data = [{
            "id": cat.id,
            "name": cat.name,
            "created_at": cat.created_at.isoformat(),
            "created": cat.created.isoformat() if cat.created else None,
            "updated": cat.updated.isoformat() if cat.updated else None,
        } for cat in categories]

        async with redis_cache.session() as redis:
            await redis.setex("categories_all", CATEGORY_TTL,
                              json.dumps(serialized_data))

        return categories
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {str(e)}")
        if session.in_transaction():
            await session.rollback()
        raise


async def orm_create_categories(session: AsyncSession,
                                categories: List[str]) -> int:
    if not categories:
        logger.warning("Попытка добавления пустого списка категорий")
        return 0

    logger.info(f"Начало обработки {len(categories)} категорий")
    try:
        existing = await session.execute(
            select(Category.name).where(Category.name.in_(categories))
        )
        existing_names = {name for name in existing.scalars()}

        new_categories = [Category(name=name) for name in categories if
                          name not in existing_names]
        if not new_categories:
            logger.info("Все категории уже существуют в базе")
            return 0

        session.add_all(new_categories)
        await session.commit()

        await CacheInvalidator.invalidate_by_pattern("categories:*")
        async with redis_cache.session() as redis:
            await redis.delete("categories_all")

        logger.info(f"Успешно добавлено {len(new_categories)} новых категорий")
        return len(new_categories)
    except Exception as e:
        logger.critical(
            f"Критическая ошибка при добавлении категорий: {str(e)}")
        await session.rollback()
        raise
