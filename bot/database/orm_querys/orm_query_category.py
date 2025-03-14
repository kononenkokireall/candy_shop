from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Category
import logging

logger = logging.getLogger(__name__)


async def orm_get_categories(session: AsyncSession) -> Sequence[Category]:
    """
    Получает все категории товаров из базы данных.

    Параметры:
        session (AsyncSession): Асинхронная сессия для работы с БД

    Возвращает:
        List[Category]: Список объектов Category

    Исключения:
        Прокидывает исключения уровня БД
    """
    logger.info("Запрос всех категорий товаров")

    try:
        result = await session.execute(select(Category))
        categories = result.scalars().all()

        logger.debug(f"Найдено {len(categories)} категорий")
        return categories

    except Exception as e:
        logger.error(f"Ошибка получения категорий: {str(e)}")
        await session.rollback()
        raise


async def orm_create_categories(session: AsyncSession, categories: List[str]) -> int:
    """
    Создает новые уникальные категории в базе данных.
    """
    if not categories:
        logger.warning("Попытка добавления пустого списка категорий")
        return 0

    logger.info(f"Начало обработки {len(categories)} категорий")

    try:
        # Проверка существующих категорий
        existing = await session.execute(
            select(Category.name).where(Category.name.in_(categories))
        )
        existing_names = {name for name in existing.scalars()}

        # Фильтрация новых категорий
        new_categories = [
            Category(name=name)
            for name in categories
            if name not in existing_names
        ]

        if not new_categories:
            logger.info("Все категории уже существуют в базе")
            return 0

        # Пакетное добавление
        session.add_all(new_categories)
        await session.commit()

        logger.info(f"Успешно добавлено {len(new_categories)} новых категорий")
        return len(new_categories)

    except Exception as e:
        logger.critical(f"Критическая ошибка при добавлении категорий: {str(e)}")
        await session.rollback()
        raise