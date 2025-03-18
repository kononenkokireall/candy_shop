from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Category
import logging

# Настройка логгера для данного модуля
logger = logging.getLogger(__name__)


async def orm_get_categories(session: AsyncSession) -> Sequence[Category]:
    """
    Получает все категории товаров из базы данных.

    Параметры:
      - session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
      - Sequence[Category]: Список объектов Category,
       содержащих все найденные категории.

    Исключения:
      - Прокидывает исключения, возникшие при выполнении запроса к базе данных.
    """
    logger.info("Запрос всех категорий товаров")

    try:
        # Формируем запрос для получения всех категорий
        result = await session.execute(select(Category))
        # Извлекаем все объекты Category из результата запроса
        categories = result.scalars().all()

        logger.debug(f"Найдено {len(categories)} категорий")
        return categories

    except Exception as e:
        # Логирование ошибки и откат транзакции в случае исключения
        logger.error(f"Ошибка получения категорий: {str(e)}")
        await session.rollback()
        raise


async def orm_create_categories(session: AsyncSession,
                                categories: List[str]) -> int:
    """
    Создает новые уникальные категории в базе данных.

    Параметры:
      - session (AsyncSession): Асинхронная сессия для работы с базой данных.
      - categories (List[str]): Список имен категорий,
       которые необходимо добавить.

    Возвращает:
      - int: Количество успешно добавленных новых категорий.

    Исключения:
      - Прокидывает исключения, возникшие при выполнении запроса к базе данных.
    """
    if not categories:
        # Если передан пустой список категорий,
        # логируем предупреждение и выходим
        logger.warning("Попытка добавления пустого списка категорий")
        return 0

    logger.info(f"Начало обработки {len(categories)} категорий")

    try:
        # Проверка существующих категорий: выбираем имена из базы,
        # которые совпадают с переданными
        existing = await session.execute(
            select(Category.name).where(Category.name.in_(categories))
        )
        # Собираем существующие имена в множество для быстрого поиска
        existing_names = {name for name in existing.scalars()}

        # Фильтруем список: оставляем только те категории, которых нет в базе
        new_categories = [
            Category(name=name)
            for name in categories if name not in existing_names
        ]

        if not new_categories:
            logger.info("Все категории уже существуют в базе")
            return 0

        # Пакетное добавление новых категорий в сессию
        session.add_all(new_categories)
        # Фиксируем изменения в базе данных
        await session.commit()

        logger.info(f"Успешно добавлено {len(new_categories)} новых категорий")
        return len(new_categories)

    except Exception as e:
        # В случае ошибки логируем критическую ошибку,
        # откатываем транзакцию и пробрасываем исключение
        logger.critical(f"Критическая ошибка при добавлении категорий:"
                        f" {str(e)}")
        await session.rollback()
        raise
