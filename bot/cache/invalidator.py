"""
Инвалидация кэша: точечно и по паттерну SCAN.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from cache.redis import get_redis

logger = logging.getLogger(__name__)


class CacheInvalidator:
    """Helpers to delete Redis keys safely."""

    # ---------------- direct keys ----------------
    @staticmethod
    async def invalidate(keys: List[str]) -> None:
        if not keys:
            return
        try:
            async with get_redis() as redis:
                deleted = await redis.delete(*keys)
            logger.debug("Deleted %s keys: %s", deleted, keys)
        except Exception as exc:  # pragma: no cover
            logger.error("Invalidate error keys=%s: %s", keys, exc)

    # ---------------- by pattern -----------------
    @staticmethod
    async def invalidate_by_pattern(pattern: str) -> None:
        cursor = 0
        total_deleted = 0
        try:
            async with get_redis() as redis:
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern,
                                                    count=1000)
                    if keys:
                        total_deleted += await redis.delete(*keys)
                    if cursor == 0:
                        break
            logger.info("Deleted %s keys by pattern '%s'", total_deleted,
                        pattern)
        except Exception as exc:  # pragma: no cover
            logger.error("Pattern invalidate error '%s': %s", pattern, exc)

    # ---------------- user helper ---------------
    @staticmethod
    async def invalidate_user_cache(user_id: int, cache_types: Optional[
        List[str]] = None) -> None:
        cache_types = cache_types or ["cart", "favorites", "orders"]
        keys = [f"{t}:{user_id}" for t in cache_types]
        await CacheInvalidator.invalidate(keys)
