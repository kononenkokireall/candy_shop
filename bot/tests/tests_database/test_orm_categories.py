from unittest.mock import AsyncMock, Mock
import logging
import pytest

from database.models import Category
from database.orm_querys.orm_query_category import orm_get_categories, orm_create_categories

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Тесты для orm_get_categories
@pytest.mark.asyncio
async def test_orm_get_categories_with_data():
    """Получение всех категорий при их наличии в базе"""
    mock_categories = [Mock(), Mock()]
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(
        scalars=Mock(return_value=Mock(all=Mock(return_value=mock_categories))))

    result = await orm_get_categories(mock_session)

    assert len(result) == 2
    logger.info.assert_any_call("Запрос всех категорий товаров")
    logger.info.assert_any_call("Найдено 2 категорий")


@pytest.mark.asyncio
async def test_orm_get_categories_empty():
    """Получение категорий из пустой таблицы"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(scalars=Mock(return_value=Mock(all=Mock(return_value=[]))))

    result = await orm_get_categories(mock_session)

    assert len(result) == 0
    logger.info.assert_any_call("Найдено 0 категорий")


# Тесты для orm_create_categories
@pytest.mark.asyncio
async def test_orm_create_categories_new():
    """Добавление категорий в пустую таблицу"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=None))

    categories_list = ["Электроника", "Одежда"]
    await orm_create_categories(mock_session, categories_list)

    mock_session.add_all.assert_called_once()
    added_categories = mock_session.add_all.call_args[0][0]
    assert len(added_categories) == 2
    assert all(isinstance(cat, Category) for cat in added_categories)
    mock_session.commit.assert_awaited_once()
    logger.info.assert_called_with("Добавлены 2 новых категорий: ['Электроника', 'Одежда']")


@pytest.mark.asyncio
async def test_orm_create_categories_existing():
    """Попытка добавить категории в непустую таблицу"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=True))

    await orm_create_categories(mock_session, ["Книги"])

    mock_session.add_all.assert_not_called()
    logger.warning.assert_called_with("Категории уже существуют. Добавление отменено.")


@pytest.mark.asyncio
async def test_orm_create_categories_empty_list():
    """Попытка добавить пустой список категорий"""
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=None))

    await orm_create_categories(mock_session, [])

    mock_session.add_all.assert_not_called()  # Даже если таблица пуста, нечего добавлять
    logger.info.assert_not_called()  # Сообщение о добавлении не должно быть вызвано