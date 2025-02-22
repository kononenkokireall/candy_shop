import pytest
from unittest.mock import MagicMock
from aiogram import Dispatcher, Bot
from database.engine import engine


@pytest.fixture
def bot():
    return MagicMock(spec=Bot)

@pytest.fixture
def dispatcher():
    return Dispatcher()

@pytest.fixture(autouse=True)
def setup_db():
    engine.connect()
    yield
    engine.disconnect()