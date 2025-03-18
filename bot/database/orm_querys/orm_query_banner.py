import logging
from typing import Dict, Optional, List, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner

# Настраиваем логгер для модуля.
# Все сообщения логгируются с использованием этого логгера.
logger = logging.getLogger(__name__)


############### Работа с баннерами (информационными страницами) ###############


async def orm_add_banner_description(
        session: AsyncSession,
        data: Dict[str, str]
) -> None:
    """
    Функция проверяет, существуют ли уже записи в таблице Banner.
    Если записей нет, добавляет новые баннеры с описаниями,
     полученными из словаря `data`.

    Параметры:
      - session: асинхронная сессия SQLAlchemy для работы с базой данных.
      - data: словарь, где ключи — имена баннеров (например, 'main', 'about'),
              а значения — их описание.
    """
    logger.info("Проверка существования баннеров в базе")
    try:
        # Формируем запрос для получения всех записей из таблицы Banner
        query = select(Banner)
        result = await session.execute(query)

        # Если хотя бы одна запись существует,
        # дальнейшее добавление не требуется.
        if result.first():
            logger.info("Баннеры уже существуют,"
                        " добавление новых не требуется")
            return

        logger.info(f"Добавление {len(data)} новых баннеров")
        # Создаем объекты Banner на основе данных из словаря.
        banners = [
            Banner(name=name, description=description)
            for name, description in data.items()
        ]
        # Добавляем созданные объекты в сессию.
        session.add_all(banners)
        # Фиксируем изменения в базе данных.
        await session.commit()
        logger.info("Баннеры успешно добавлены")
    except Exception as e:
        # Логируем исключение,
        # откатываем транзакцию и пробрасываем ошибку дальше.
        logger.exception(f"Ошибка при добавлении баннеров {e}")
        await session.rollback()
        raise


async def orm_change_banner_image(
        session: AsyncSession,
        name: str,
        image: str,
        admin_link: Optional[str] = None
) -> None:
    """
    Функция изменяет изображение и (опционально)
     ссылку администратора для баннера с заданным именем.

    Параметры:
      - session: асинхронная сессия SQLAlchemy.
      - name: имя баннера, для которого необходимо изменить изображение.
      - image: новое изображение (URL или путь).
      - admin_link: опциональная ссылка для администратора.
    """
    logger.info(f"Обновление изображения баннера '{name}'")
    try:
        # Формируем запрос для обновления записи в таблице Banner,
        # где имя совпадает с переданным.
        query = (
            update(Banner)
            .where(Banner.name == name)
            .values(image=image, admin_link=admin_link)
        )
        result = await session.execute(query)
        await session.commit()

        # Проверяем количество затронутых строк,
        # чтобы убедиться, что запись была обновлена.
        if result.rowcount and result.rowcount > 0:
            logger.info(f"Изображение баннера '{name}' успешно обновлено")
        else:
            logger.warning(f"Баннер '{name}' не найден или данные не изменены")
    except Exception as e:
        # Логируем ошибку с информацией о баннере,
        # откатываем транзакцию и пробрасываем исключение.
        logger.exception(f"Ошибка при обновлении изображения баннера {e}"
                         f" '{name}'")
        await session.rollback()
        raise


async def orm_get_banner(
        session: AsyncSession,
        page: str)\
        -> Optional[Banner]:
    """
    Функция возвращает баннер для указанной страницы.

    Параметры:
      - session: асинхронная сессия SQLAlchemy.
      - page: имя страницы или баннера, который необходимо получить.

    Возвращает:
      - Объект баннера, если он найден, иначе None.
    """
    logger.info(f"Запрос баннера для страницы '{page}'")
    try:
        # Формируем запрос для получения баннера по его имени (page).
        query = select(Banner).where(Banner.name == page)
        result = await session.execute(query)
        banner = result.scalar()  # Получаем один объект баннера

        if banner:
            logger.info(f"Баннер '{page}' найден")
        else:
            logger.warning(f"Баннер '{page}' не найден")

        return banner
    except Exception as e:
        # Логируем ошибку при выполнении запроса и пробрасываем исключение.
        logger.exception(f"Ошибка при запросе баннера для страницы {e}"
                         f" '{page}'")
        raise


async def orm_get_info_pages(
        session: AsyncSession,
        page: Optional[str] = None) -> Sequence[Banner]:
    """
    Функция возвращает список информационных баннеров.
    Если параметр page указан,
     возвращает только баннер для конкретной страницы.

    Параметры:
      - session: асинхронная сессия SQLAlchemy.
      - page: опциональное имя страницы для фильтрации баннеров.

    Возвращает:
      - Список объектов баннеров.
    """
    if page:
        logger.info(f"Запрос информации о баннере '{page}'")
    else:
        logger.info("Запрос всех информационных баннеров")

    try:
        # Формируем базовый запрос для получения всех баннеров.
        query = select(Banner)
        # Если указан параметр page, добавляем фильтр по имени баннера.
        if page:
            query = query.where(Banner.name == page)

        result = await session.execute(query)
        # Получаем все объекты баннеров в виде списка.
        banners = result.scalars().all()

        if banners:
            logger.info(f"Найдено {len(banners)} баннеров")
        else:
            logger.warning("Баннеры не найдены")

        return banners
    except Exception as e:
        # Логируем ошибку при выполнении запроса и пробрасываем исключение.
        logger.exception(f"Ошибка при получении информационных баннеров {e} ")
        raise
