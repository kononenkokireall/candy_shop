"""
Redis connection manager (v2).

* Один пул Redis, размер задаётся `REDIS_POOL_SIZE`.
* TLS-проверка сертификата включена; отключается переменной
  `REDIS_INSECURE_SSL=1`.
* Функции:
    • init_pool()   – создать пул (лениво).
    • get_redis()   – async-context, отдаёт клиент из пула.
    • close_pool()  – закрыть на shut-down.
* `redis_cache.session()` – adapter для обратной совместимости.
"""
from __future__ import annotations

import os
import ssl
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Final

from redis.asyncio import Redis

__all__ = ["init_pool", "get_redis", "close_pool", "redis_cache"]

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------
REDIS_URL: Final[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_CONN: Final[int] = int(os.getenv("REDIS_POOL_SIZE", "10"))

ssl_kwargs: dict[str, object] = {}
if REDIS_URL.startswith("rediss://"):
    ssl_kwargs["ssl_cert_reqs"] = (
        ssl.CERT_NONE if os.getenv("REDIS_INSECURE_SSL") == "1"
        else ssl.CERT_REQUIRED
    )

# ---------------------------------------------------------------------------
# Пул (singleton)
# ---------------------------------------------------------------------------
_pool: Redis | None = None


async def init_pool() -> Redis:
    """Создаёт глобальный пул, если он ещё не создан."""
    global _pool  # noqa: PLW0603
    if _pool is None:
        _pool = Redis.from_url(
            REDIS_URL,
            max_connections=MAX_CONN,
            decode_responses=True,
            **ssl_kwargs,
        )
        await _pool.ping()  # ленивый тест соединения
    return _pool


@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis, None]:
    """Контекст-менеджер, возвращающий клиент Redis из пула."""
    pool = await init_pool()
    try:
        yield pool
    finally:
        # Пул живёт всё время приложения
        pass


async def close_pool() -> None:
    """Закрыть соединения (вызывайте при завершении приложения)."""
    global _pool  # noqa: PLW0603
    if _pool:
        await _pool.close()
        await _pool.connection_pool.disconnect()
        _pool = None


# ---------------------------------------------------------------------------
# Back-combat adapter  (оставляем вызов redis_cache.session())
# ---------------------------------------------------------------------------
class _RedisCacheAdapter:  # pylint: disable=too-few-public-methods
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[Redis, None]:
        async with get_redis() as redis:
            yield redis


redis_cache = _RedisCacheAdapter()  # экспорт для старого кода
