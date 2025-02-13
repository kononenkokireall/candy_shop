from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine)

from dotenv import find_dotenv, load_dotenv
# Импорты моделей (базовая мета дата SQLAlchemy)
from database.models import Base

# Импорты функций для работы с БД
from database.orm_querys.orm_query_banner import orm_add_banner_description
from database.orm_querys.orm_query_category import orm_create_categories


# Импорты данных для заполнения базы
from common.texts_for_db import (
    categories_goods,
    description_for_info_pages
)

from utilit.config import database_url

load_dotenv(find_dotenv())

# Создание асинхронного движка для работы с базой данных. URL берется из переменной окружения.
engine = create_async_engine(database_url)

# Создание фабрики сессий (session maker) для управления асинхронными сессиями.
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Функция для создания базы данных и первоначального заполнения данными.
async def create_db():
    """
    Создает все таблицы в базе данных и заполняет ее начальными данными (категории и описания баннеров).
    """
    # Открываем подключение для создания таблиц
    async with engine.begin() as conn:
        # Создаем таблицы на основе метаданных моделей
        await conn.run_sync(Base.metadata.create_all)

    # Заполнение базы начальными данными (категории и описания страниц)
    async with session_maker() as session:
        # Заполняем категории товаров
        await orm_create_categories(session, categories_goods)
        # Заполняем баннеры для страниц
        await orm_add_banner_description(session, description_for_info_pages)


# Функция для удаления базы данных (если нужно).
async def drop_db():
    """
    Удаляет все таблицы из базы данных.
    """
    # Открываем подключение для удаления таблиц
    async with engine.begin() as conn:
        # Удаляем все таблицы
        await conn.run_sync(Base.metadata.drop_all)
