import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner

# Настраиваем логгер
logger = logging.getLogger(__name__)


############### Работа с баннерами (информационными страницами) ###############

async def orm_add_banner_description(session: AsyncSession, data: dict):
    """
    Проверяем существование записей в таблице Banner. Если записей нет, добавляем новые
    с описаниями из словаря `data`. Ключи словаря — имена пунктов (например, main, about),
    значения — их описание.
    """
    logger.info("Проверка существования баннеров в базе")

    query = select(Banner)
    result = await session.execute(query)

    if result.first():
        logger.info("Баннеры уже существуют, добавление новых не требуется")
        return

    logger.info(f"Добавление {len(data)} новых баннеров")
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()
    logger.info("Баннеры успешно добавлены")


async def orm_change_banner_image(session: AsyncSession, name: str, image: str, admin_link: str | None = None):
    """
    Изменяет изображение и (опционально) ссылку администратора для баннера с заданным именем.
    """
    logger.info(f"Обновление изображения баннера '{name}'")

    query = update(Banner).where(Banner.name == name).values(image=image, admin_link=admin_link)
    result = await session.execute(query)
    await session.commit()

    if result.rowcount() > 0:
        logger.info(f"Изображение баннера '{name}' успешно обновлено")
    else:
        logger.warning(f"Баннер '{name}' не найден или данные не изменены")


async def orm_get_banner(session: AsyncSession, page: str):
    """
    Возвращает баннер для указанной страницы.
    """
    logger.info(f"Запрос баннера для страницы '{page}'")

    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    banner = result.scalar()

    if banner:
        logger.info(f"Баннер '{page}' найден")
    else:
        logger.warning(f"Баннер '{page}' не найден")

    return banner


async def orm_get_info_pages(session: AsyncSession, page: str | None = None):
    """
    Возвращает список информационных баннеров.
    Если `page` указан, возвращает только баннер для конкретной страницы.
    """
    if page:
        logger.info(f"Запрос информации о баннере '{page}'")
    else:
        logger.info("Запрос всех информационных баннеров")

    query = select(Banner)
    if page:
        query = query.where(Banner.name == page)

    result = await session.execute(query)
    banners = result.scalars().all()

    if banners:
        logger.info(f"Найдено {len(banners)} баннеров")
    else:
        logger.warning("Баннеры не найдены")

    return banners
