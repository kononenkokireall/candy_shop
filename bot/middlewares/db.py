from typing import Any, Dict

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DBSessionMiddleware(BaseMiddleware):
    """
    Даёт хэндлерам SQLAlchemy-сессию (data["session"]).
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(self, handler, event, data: Dict[str, Any]):
        async with self.session_maker() as session:
            # кладём сессию в DI-контейнер
            data["session"] = session

            # оставляем всё, что действительно требуется aiogram’у
            filtered = {
                k: v
                for k, v in data.items()
                # убираем только «тяжёлые» или дублирующие объекты,
                # которые хэндлерам никогда не нужны
                if k not in {"dispatcher", "event_context", "update"}
            }

            try:
                # ВАЖНО: передаём одним словарём вторым позиционным
                result = await handler(event, filtered)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
