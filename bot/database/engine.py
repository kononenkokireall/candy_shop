import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from common.texts_for_db import categories_goods, description_for_info_pages
# Импорты моделей и данных
from database.models import Base
from database.orm_querys.orm_query_banner import orm_add_banner_description
from database.orm_querys.orm_query_category import orm_create_categories
from utilit.config import database_url

# Настройка логирования ДО создания движка
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Создание асинхронного движка с явным указанием пула соединений
engine = create_async_engine(
    database_url,
    echo=True,  # В продакшене лучше отключить
    pool_size=10,  # Рекомендуемые параметры пула
    max_overflow=20,
    pool_recycle=3600,
)

# Фабрика сессий с явными параметрами
session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Правильно для большинства случаев
    autoflush=False,  # Добавлено для безопасности
)

async def create_db() -> None:
    """Создание и наполнение базы данных с обработкой ошибок"""
    try:
        logger.info("Начало создания таблиц...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Таблицы успешно созданы")

        logger.info("Начало заполнения данных...")
        async with session_maker() as session:
            try:
                await orm_create_categories(session, categories_goods)
                await orm_add_banner_description(session, description_for_info_pages)
                await session.commit()
                logger.info("Данные успешно добавлены")
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Ошибка при заполнении данных: {str(e)}")
                raise

    except SQLAlchemyError as e:
        logger.critical(f"Критическая ошибка при создании БД: {str(e)}")
        raise

async def drop_db() -> None:
    """Удаление таблиц с обработкой ошибок"""
    try:
        logger.info("Начало удаления таблиц...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Таблицы успешно удалены")
    except SQLAlchemyError as e:
        logger.critical(f"Ошибка при удалении таблиц: {str(e)}")
        raise

async def dispose_engine() -> None:
    """Корректное закрытие соединений"""
    try:
        logger.info("Закрытие пула соединений...")
        await engine.dispose()
        logger.info("Пул соединений успешно закрыт")
    except Exception as e:
        logger.error(f"Ошибка при закрытии пула: {str(e)}")
        raise
