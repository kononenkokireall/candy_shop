import logging
from sqlalchemy.ext.asyncio import (AsyncSession,
                                    async_sessionmaker,
                                    create_async_engine)

# Импорты моделей (базовая мета дата SQLAlchemy)
from database.models import Base

# Импорты функций для работы с БД
from database.orm_querys.orm_query_banner import orm_add_banner_description
from database.orm_querys.orm_query_category import orm_create_categories

# Импорты данных для заполнения базы
from common.texts_for_db import categories_goods, description_for_info_pages
from utilit.config import database_url

# Создание асинхронного движка для работы с базой данных.
# URL берется из переменной окружения.
engine = create_async_engine(database_url, echo=True)

# Создание фабрики сессий (session maker) для управления асинхронными сессиями.
session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Функция для создания базы данных и первоначального заполнения данными.
async def create_db() -> None:
    """
    Создает все таблицы в базе данных
     и заполняет ее начальными данными (категории и описания баннеров).
    """
    logging.info("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        logging.info("Соединение с базой данных установлено.")
        await conn.run_sync(Base.metadata.create_all)
        logging.info("Таблицы созданы.")

    logging.info("Заполнение базы начальными данными...")
    async with session_maker() as session:
        logging.info("Сессия создана.")
        await orm_create_categories(session, categories_goods)
        await orm_add_banner_description(session, description_for_info_pages)
        logging.info("Данные добавлены.")
    logging.info("Сессия закрыта.")


# Функция для удаления базы данных (если нужно).
async def drop_db() -> None:
    """
    Удаляет все таблицы из базы данных.
    """
    logging.info("Удаление таблиц из базы данных...")
    async with engine.begin() as conn:
        logging.info("Соединение с базой данных установлено.")
        await conn.run_sync(Base.metadata.drop_all)
        logging.info("Таблицы удалены.")


# Функция для закрытия пула соединений движка.
async def dispose_engine() -> None:
    """
    Закрывает пул соединений движка.
    """
    logging.info("Закрытие пула соединений...")
    await engine.dispose()
    logging.info("Пул соединений закрыт.")
