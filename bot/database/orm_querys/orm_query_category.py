############################ Категории ######################################
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category


# Получение всех категорий товаров
async def orm_get_categories(session: AsyncSession):
    """
    Возвращает список всех категорий в базе данных.
    """
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


# Создание новых категорий
async def orm_create_categories(session: AsyncSession, categories: list):
    """
    Добавляет новые категории. Если в таблице уже есть записи, ничего не происходит.
    """
    query = select(Category)
    result = await session.execute(query)
    if result.first():  # Проверяем, существуют ли категории
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()
