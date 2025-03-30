"""
Инвалидация кэша с использованием Redis SCAN для больших наборов данных
"""

from typing import List
from cache.redis import redis_cache
import logging

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """
    Безопасная инвалидация кэша через SCAN-итератор вместо KEYS
    Решает проблемы:
    - Блокировка Redis при больших наборах ключей
    - Пакетная обработка для оптимизации производительности
    """

    @staticmethod
    async def invalidate(keys: List[str]) -> None:
        """Пакетное удаление по прямым ключам"""
        async with redis_cache.session() as redis:
            if keys:
                deleted = await redis.delete(*keys)
                logger.debug(f"Deleted {deleted} keys: {keys}")

    @staticmethod
    async def invalidate_by_pattern(pattern: str) -> None:
        """Итеративное удаление по паттерну с использованием SCAN"""
        async with redis_cache.session() as redis:
            cursor, deleted_total = "0", 0
            while cursor != 0:
                # Получаем ключи порциями по 1000 для избежания блокировок
                cursor, keys = await redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=1000
                )
                if keys:
                    deleted = await redis.delete(*keys)
                    deleted_total += deleted
                    logger.debug(
                        f"Deleted {deleted} keys by pattern {pattern}")

            logger.info(f"Total deleted by {pattern}: {deleted_total}")
