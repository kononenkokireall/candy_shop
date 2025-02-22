import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category

# Настройка логгера
logger = logging.getLogger(__name__)


# Получение всех категорий товаров
async def orm_get_categories(session: AsyncSession):
    """
    Возвращает список всех категорий в базе данных.
    """
    logger.info("Запрос всех категорий товаров")

    query = select(Category)
    result = await session.execute(query)
    categories = result.scalars().all()

    logger.info(f"Найдено {len(categories)} категорий")
    return categories


# Создание новых категорий
async def orm_create_categories(session: AsyncSession, categories: list):
    """
    Добавляет новые категории. Если в таблице уже есть записи, ничего не происходит.
    """
    logger.info("Попытка добавления новых категорий")

    query = select(Category)
    result = await session.execute(query)

    if result.first():  # Проверяем, существуют ли категории
        logger.warning("Категории уже существуют. Добавление отменено.")
        return

    session.add_all([Category(name=name) for name in categories])
    await session.commit()
    logger.info(f"Добавлены {len(categories)} новых категорий: {categories}")
