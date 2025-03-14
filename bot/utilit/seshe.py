import asyncio
import logging
from datetime import datetime
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (например, DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Общий кэш для всех вызовов функции
_products_cache = {}
_cache_lock = asyncio.Lock()
_CACHE_TTL = 300  # 5 минут в секундах


def async_cache(ttl: int = _CACHE_TTL):
    def decorator(func):
        @wraps(func)
        async def wrapper(session: AsyncSession, category_id: int, *args, **kwargs):
            current_time = datetime.now()
            async with _cache_lock:  # Блокировка для поток-безопасности
                # Проверяем кэш
                cache_entry = _products_cache.get(category_id)

                if cache_entry and (current_time - cache_entry['timestamp']).seconds < ttl:
                    logger.debug(f"Возвращаем кэшированные товары для категории {category_id}")
                    return cache_entry['data']

                # Если кэш устарел или отсутствует
                logger.debug(f"Обновление кэша для категории {category_id}")
                try:
                    data = await func(session, category_id, *args, **kwargs)
                    _products_cache[category_id] = {
                        'data': data,
                        'timestamp': current_time
                    }
                    return data
                except Exception as e:
                    # Возвращаем устаревшие данные, если есть
                    if cache_entry:
                        logger.warning(f"Используем устаревший кэш из-за ошибки: {str(e)}")
                        return cache_entry['data']
                    raise

        return wrapper

    return decorator

# Пример функции для инвалидации кэша
async def invalidate_products_cache(category_id: int):
    async with _cache_lock:
        if category_id in _products_cache:
            del _products_cache[category_id]
            logger.debug(f"Кэш для категории {category_id} очищен")