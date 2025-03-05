import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, Base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from common.texts_for_db import categories_goods, description_for_info_pages
from database.engine import create_db, drop_db, dispose_engine


# Фикстуры для моков
@pytest.fixture
def mock_engine():
    engine_mock = MagicMock(spec=AsyncEngine)
    engine_mock.begin = MagicMock(return_value=AsyncMock())
    return engine_mock

@pytest.fixture
def mock_session_maker():
    return MagicMock(spec=async_sessionmaker)

@pytest.mark.asyncio
async def test_create_db(mock_engine, mock_session_maker):
    """Проверка создания таблиц и заполнения данных"""
    # Мокируем зависимости
    with patch("your_module.engine", mock_engine), \
         patch("your_module.session_maker", mock_session_maker), \
         patch("your_module.orm_create_categories") as mock_create_cats, \
         patch("your_module.orm_add_banner_description") as mock_add_banner, \
         patch("your_module.logging.info") as mock_logging:

        # Вызываем тестируемую функцию
        await create_db()

        # Проверка создания таблиц
        mock_engine.begin.assert_called_once()
        conn = mock_engine.begin.return_value
        conn.run_sync.assert_awaited_once_with(Base.metadata.create_all)

        # Проверка заполнения данных
        mock_session_maker.assert_called_once()
        session = mock_session_maker.return_value
        mock_create_cats.assert_awaited_once_with(session, categories_goods)
        mock_add_banner.assert_awaited_once_with(session, description_for_info_pages)

        # Проверка логирования
        expected_logs = [
            call("Создание таблиц в базе данных..."),
            call("Соединение с базой данных установлено."),
            call("Таблицы созданы."),
            call("Заполнение базы начальными данными..."),
            call("Сессия создана."),
            call("Данные добавлены."),
            call("Сессия закрыта.")
        ]
        mock_logging.assert_has_calls(expected_logs, any_order=False)

@pytest.mark.asyncio
async def test_drop_db(mock_engine):
    """Проверка удаления таблиц"""
    with patch("your_module.engine", mock_engine), \
         patch("your_module.logging.info") as mock_logging:

        await drop_db()

        mock_engine.begin.assert_called_once()
        conn = mock_engine.begin.return_value
        conn.run_sync.assert_awaited_once_with(Base.metadata.drop_all)

        expected_logs = [
            call("Удаление таблиц из базы данных..."),
            call("Соединение с базой данных установлено."),
            call("Таблицы удалены.")
        ]
        mock_logging.assert_has_calls(expected_logs)

@pytest.mark.asyncio
async def test_dispose_engine(mock_engine):
    """Проверка закрытия пула соединений"""
    with patch("your_module.engine", mock_engine), \
         patch("your_module.logging.info") as mock_logging:

        await dispose_engine()

        mock_engine.dispose.assert_awaited_once()
        mock_logging.assert_has_calls([
            call("Закрытие пула соединений..."),
            call("Пул соединений закрыт.")
        ])