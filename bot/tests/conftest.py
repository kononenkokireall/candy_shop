from datetime import datetime

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Chat, CallbackQuery, Message
from sqlalchemy.ext.asyncio import create_async_engine

from database.models import User, Base
from keyboards.inline_main import MenuCallBack
from middlewares.db import DataBaseSession
from database.engine import session_maker
from main import user_private_router, user_group_router, admin_router
from utilit.notification import NotificationService


# Fixtures для mock сессии базы данных
@pytest.fixture(autouse=True)
def mock_db_session(monkeypatch):
    mock_session = AsyncMock()
    monkeypatch.setattr(session_maker, "__call__", AsyncMock(return_value=mock_session))
    return mock_session


# Fixtures для бота
@pytest.fixture(scope="session")
async def bot() -> AsyncGenerator[Bot, None]:
    bot = Bot(token="test:token", validate_token=False)
    yield bot
    await bot.session.close()


# Fixtures для диспетчера с роутер и middleware
@pytest.fixture()
async def dispatcher(mock_db_session) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутер как в main.py
    dp.include_router(user_private_router)
    dp.include_router(user_group_router)
    dp.include_router(admin_router)

    # Добавляем middleware для БД
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    return dp


# Фикстура для сообщения пользователя
@pytest.fixture()
def private_message() -> dict:
    return {
        "message": {
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 123, "first_name": "TestUser"},
            "text": "/start"
        }
    }


# Fixtures для сообщения в группе
@pytest.fixture()
def group_message() -> dict:
    return {
        "message": {
            "chat": {"id": -456, "type": "group"},
            "from": {"id": 123, "first_name": "TestUser"},
            "text": "/help"
        }
    }

# Добавьте новые Fixtures
@pytest.fixture
def mock_notification_service():
    return AsyncMock(spec=NotificationService)

@pytest.fixture
def mock_callback_query(bot):
    user = User(id=123, first_name="Test", is_bot=False)
    chat = Chat(id=123, type="private")
    return CallbackQuery(
        id="test_id",
        from_user=user,
        chat_instance="test_chat",
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=chat,
            text="/start"
        ),
        data=MenuCallBack().pack()
    )

# Фикстура для администраторского сообщения
@pytest.fixture
def admin_message():
    return Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=123, type="private"),
        from_user=User(id=456, is_bot=False, first_name="Admin")
    )

# Фикстура для администраторского callback
@pytest.fixture
def admin_callback(bot):
    return CallbackQuery(
        id="test_admin_callback",
        from_user=User(id=456, is_bot=False, first_name="Admin"),
        message=Message(message_id=1, chat=Chat(id=789, type="private")),
        data="test_data"
    )


@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch):
    # Подменяем URL базы данных на тестовую
    monkeypatch.setattr("bot.database.engine.database_url", "sqlite+aiosqlite:///:memory:")

    # Сбрасываем mock перед каждым тестом
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    Base.metadata.create_all = MagicMock()
    Base.metadata.drop_all = MagicMock()