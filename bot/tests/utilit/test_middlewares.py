import pytest
from unittest.mock import AsyncMock, MagicMock, call
from aiogram.types import TelegramObject

from middlewares.db import DataBaseSession


@pytest.mark.asyncio
async def test_middleware_creates_session_and_adds_to_data():
    """Проверка создания сессии и добавления её в data"""
    # Arrange
    mock_session = AsyncMock()
    mock_session_pool = MagicMock()
    mock_session_pool.return_value = mock_session  # session_pool() возвращает сессию

    middleware = DataBaseSession(mock_session_pool)
    handler = AsyncMock(return_value="handler_result")
    event = TelegramObject()
    data = {}

    # Act
    result = await middleware(handler, event, data)

    # Assert
    # Проверка создания сессии
    mock_session_pool.assert_called_once()

    # Проверка работы контекстного менеджера
    mock_session.__aenter__.assert_awaited_once()
    mock_session.__aexit__.assert_awaited_once()

    # Проверка добавления сессии в data
    assert data["session"] is mock_session

    # Проверка вызова handler с обновленными данными
    handler.assert_awaited_once_with(event, data)

    # Проверка возврата результата handler
    assert result == "handler_result"


@pytest.mark.asyncio
async def test_middleware_closes_session_on_handler_error():
    """Проверка закрытия сессии при ошибке в обработчике"""
    # Arrange
    mock_session = AsyncMock()
    mock_session_pool = MagicMock()
    mock_session_pool.return_value = mock_session

    middleware = DataBaseSession(mock_session_pool)
    handler = AsyncMock(side_effect=Exception("Test error"))
    event = TelegramObject()
    data = {}

    # Act & Assert
    with pytest.raises(Exception, match="Test error"):
        await middleware(handler, event, data)

    # Проверка закрытия сессии даже при ошибке
    mock_session.__aenter__.assert_awaited_once()
    mock_session.__aexit__.assert_awaited_once()