############### Работа с баннерами (информационными страницами) ###############
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Banner


# Функция для добавления или изменения описания баннеров
async def orm_add_banner_description(session: AsyncSession, data: dict):
    """
    Проверяем существование записей в таблице Banner. Если записей нет, добавляем новые
    с описаниями из словаря `data`. Ключи словаря — имена пунктов (например, main, about),
    значения — их описание.
    """
    query = select(Banner)  # Проверяем существующие записи
    result = await session.execute(query)
    if result.first():  # Если записи уже существуют, ничего не делаем
        return
    # Добавляем новые баннеры
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


# Функция для изменения изображения и ссылки администратора у баннера
async def orm_change_banner_image(
        session: AsyncSession,
        name: str,
        image: str,
        admin_link: str | None = None,
):
    """
    Изменяет изображение и (опционально) ссылку администратора для баннера с заданным именем.
    """
    query = (update(Banner)
             .where(Banner.name == name)
             .values(image=image,
                     admin_link=admin_link))

    await session.execute(query)
    await session.commit()


# Функция для получения информации о баннере по его имени (странице)
async def orm_get_banner(session: AsyncSession, page: str):
    """
    Возвращает баннер для указанной страницы.
    """
    query = (select(Banner)
             .where(Banner.name == page))

    result = await session.execute(query)
    return result.scalar()


# Функция для получения всех информационных страниц или конкретной
async def orm_get_info_pages(session: AsyncSession, page: str | None = None):
    """
    Возвращает список информационных баннеров.
    Если `page` указан, возвращает только баннер для конкретной страницы.
    """
    query = select(Banner)
    if page:
        query = query.where(Banner.name == page)
    result = await session.execute(query)
    return result.scalars().all()