from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


# Класс DataBaseSession реализует middleware для работы с базой данных.
# Он наследуется от BaseMiddleware библиотеки aiogram.
class DataBaseSession(BaseMiddleware):
    # Конструктор принимает объект session_pool, который является фабрикой
    # асинхронных сессий для работы с базой данных (async_session-maker).
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    # Метод __call__ позволяет экземпляру класса DataBaseSession
    # быть вызываемым,
    # что необходимо для реализации middleware в aiogram.
    # Параметры:
    # - handler: функция-обработчик,
    # которая принимает объект TelegramObject и словарь данных,
    #   возвращая асинхронное (Awaitable) значение.
    # - event: объект события (например, сообщение), полученный от Telegram.
    # - data: словарь дополнительных данных,
    # который передается между middleware.
    async def __call__(
            self,
            handler: Callable[
                [TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        # Создаем асинхронную сессию базы данных, используя session_pool.
        # Контекстный менеджер гарантирует,
        # что сессия будет корректно закрыта после использования.
        async with self.session_pool() as session:
            # Добавляем созданную сессию в словарь данных под ключом 'session',
            # чтобы она была доступна
            # для дальнейшей обработки в функции-обработчике.
            data["session"] = session
            # Вызываем переданный обработчик (handler)
            # с объектом события и обновленным словарем данных,
            # а затем возвращаем результат его выполнения.
            return await handler(event, data)
