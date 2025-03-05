import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy import select
import logging
from database.models import User
from database.orm_querys.orm_query_user import orm_add_user

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_add_new_user_success():
    """Успешное добавление нового пользователя"""
    # Arrange
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=None))
    user_id = 123
    first_name = "Иван"
    last_name = "Иванов"
    phone = "+79001234567"

    # Act
    await orm_add_user(mock_session, user_id, first_name, last_name, phone)

    # Assert
    # Проверка запроса на существование пользователя
    mock_session.execute.assert_any_call(select(User).where(User.user_id == user_id))

    # Проверка добавления пользователя
    mock_session.add.assert_called_once()
    added_user = mock_session.add.call_args[0][0]
    assert isinstance(added_user, User)
    assert added_user.user_id == user_id
    assert added_user.first_name == first_name
    assert added_user.last_name == last_name
    assert added_user.phone == phone

    # Проверка коммита и логов
    mock_session.commit.assert_awaited_once()
    logger.info.assert_any_call(f"Пользователь {user_id} успешно добавлен в базу")


@pytest.mark.asyncio
async def test_add_existing_user():
    """Попытка добавить существующего пользователя"""
    # Arrange
    mock_session = AsyncMock()
    mock_session.execute.return_value = AsyncMock(first=Mock(return_value=Mock()))
    user_id = 456

    # Act
    await orm_add_user(mock_session, user_id)

    # Assert
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    logger.warning.assert_called_with(f"Пользователь {user_id} уже существует в базе")


@pytest.mark.asyncio
async def test_add_user_with_error():
    """Обработка ошибки при добавлении"""
    # Arrange
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Database error")
    user_id = 789

    # Act & Assert
    with pytest.raises(Exception, match="Database error"):
        await orm_add_user(mock_session, user_id)

    mock_session.rollback.assert_awaited()
    logger.exception.assert_called_with(f"Ошибка при добавлении пользователя {user_id}: Database error")