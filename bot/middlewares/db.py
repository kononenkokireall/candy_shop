from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class DataBaseSession(BaseMiddleware):
    """
    Middleware для предоставления сессии БД в каждый хенд лер.
    Создаёт сессию из session_pool и передаёт её в хенд лер через data["session"].
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Создаем сессию без начала транзакции
        async with self.session_pool() as session:
            data["session"] = session
            # Хенд лер сам управляет транзакцией, если нужно
            return await handler(event, data)
