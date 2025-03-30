"""
Конфигурация Redis для асинхронного доступа с поддержкой Heroku и SSL
"""

from redis.asyncio import Redis  # Импорт асинхронного клиента из новой версии
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import ssl  # Для корректной работы с SSL-параметрами

class RedisCache:
    """
    Менеджер пула соединений Redis с обработкой Heroku-специфичных параметров
    """

    def __init__(self):
        self.redis: Redis | None = None

    async def init_cache(self):
        """Инициализация подключения с учетом SSL"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Конфигурация SSL (для Redis Cloud/Heroku)
        ssl_config = {}
        if redis_url.startswith("rediss://"):
            ssl_config["ssl_cert_reqs"] = ssl.CERT_NONE

        self.redis = Redis.from_url(
            redis_url,
            decode_responses=True,
            **ssl_config
        )
        # Проверка подключения
        await self.redis.ping()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[Redis, None]:
        """
        Контекстный менеджер для работы с Redis.
        """
        if not self.redis:
            await self.init_cache()
        try:
            yield self.redis
        finally:
            # Очистка ресурсов при необходимости
            pass

# Глобальный экземпляр для повторного использования
redis_cache = RedisCache()