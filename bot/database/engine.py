import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base  # Импорты моделей (базовая мета дата SQLAlchemy)
from database.orm_query import orm_add_banner_description, orm_create_categories  # Импорты функций для работы с БД

from common.texts_for_db import categories_goods, description_for_info_pages  # Импорты данных для заполнения базы

# Создание асинхронного движка для работы с базой данных. URL берется из переменной окружения.
engine = create_async_engine(os.getenv('DB_URL'), echo=True)

# Создание фабрики сессий (session maker) для управления асинхронными сессиями.
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Функция для создания базы данных и первоначального заполнения данными.
async def create_db():
    """
    Создает все таблицы в базе данных и заполняет ее начальными данными (категории и описания баннеров).
    """
    # Открываем подключение для создания таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Создаем таблицы на основе метаданных моделей

    # Заполнение базы начальными данными (категории и описания страниц)
    async with session_maker() as session:
        await orm_create_categories(session, categories_goods)  # Заполняем категории товаров
        await orm_add_banner_description(session, description_for_info_pages)  # Заполняем баннеры для страниц


# Функция для удаления базы данных (если нужно).
async def drop_db():
    """
    Удаляет все таблицы из базы данных.
    """
    # Открываем подключение для удаления таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем все таблицы
