import logging
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select, update

from database.models import Banner
from database.orm_querys.orm_query_banner import orm_add_banner_description, orm_change_banner_image, orm_get_banner, \
    orm_get_info_pages

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_orm_add_banner_description_new():
    """Добавление баннеров в пустую таблицу"""
    # Arrange
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=None))
    data = {"main": "Главная страница", "about": "О нас"}

    # Act
    await orm_add_banner_description(mock_session, data)

    # Assert
    mock_session.add_all.assert_called_once()
    assert len(mock_session.add_all.call_args[0][0]) == 2
    mock_session.commit.assert_awaited_once()
    logger.info.assert_any_call("Добавление 2 новых баннеров")


@pytest.mark.asyncio
async def test_orm_add_banner_description_existing():
    """Попытка добавить баннеры в непустую таблицу"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=True))

    await orm_add_banner_description(mock_session, {})

    mock_session.add_all.assert_not_called()
    logger.info.assert_called_with("Баннеры уже существуют, добавление новых не требуется")


@pytest.mark.asyncio
async def test_orm_change_banner_image_success():
    """Успешное обновление изображения баннера"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(rowcount=1)

    await orm_change_banner_image(mock_session, "main", "new_image.jpg", "admin_link")

    expected_query = update(Banner).where(Banner.name == "main").values(
        image="new_image.jpg",
        admin_link="admin_link"
    )
    mock_session.execute.assert_awaited_once_with(expected_query)
    logger.info.assert_called_with("Изображение баннера 'main' успешно обновлено")


@pytest.mark.asyncio
async def test_orm_change_banner_image_not_found():
    """Попытка обновить несуществующий баннер"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(rowcount=0)

    await orm_change_banner_image(mock_session, "unknown", "image.jpg")

    logger.warning.assert_called_with("Баннер 'unknown' не найден или данные не изменены")


@pytest.mark.asyncio
async def test_orm_get_banner_found():
    """Успешный поиск существующего баннера"""
    mock_banner = Mock()
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=mock_banner))

    result = await orm_get_banner(mock_session, "main")

    assert result is mock_banner
    logger.info.assert_called_with("Баннер 'main' найден")


@pytest.mark.asyncio
async def test_orm_get_banner_not_found():
    """Поиск несуществующего баннера"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalar=Mock(return_value=None))

    result = await orm_get_banner(mock_session, "unknown")

    assert result is None
    logger.warning.assert_called_with("Баннер 'unknown' не найден")


@pytest.mark.asyncio
async def test_orm_get_info_pages_all():
    """Получение всех баннеров"""
    mock_banners = [Mock(), Mock()]
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(
        scalars=Mock(return_value=AsyncMock(all=Mock(return_value=mock_banners))))

    result = await orm_get_info_pages(mock_session)

    assert len(result) == 2
    logger.info.assert_called_with("Найдено 2 баннеров")


@pytest.mark.asyncio
async def test_orm_get_info_pages_filtered():
    """Фильтрация баннеров по имени страницы"""
    mock_session = AsyncMock()
    await orm_get_info_pages(mock_session, "main")

    expected_query = select(Banner).where(Banner.name == "main")
    mock_session.execute.assert_awaited_once_with(expected_query)