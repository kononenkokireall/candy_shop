from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, Coroutine, Union, Dict, List

import orjson
import logging
from cache.redis import redis_cache

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)


def model_to_dict(obj: Any) -> Union[Dict, List]:
    """Рекурсивно конвертирует ORM-объекты в словари с обработкой datetime"""
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]

    if hasattr(obj, '__table__'):
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)

            # Автоматическая обработка datetime и Decimal
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif hasattr(value, '__table__'):
                value = model_to_dict(value)  # Рекурсия для связанных объектов

            result[column.name] = value
        return result
    return obj


def dict_to_model(data: Union[Dict, List]) -> Any:
    """Конвертация словаря в объект-заглушку с восстановлением datetime"""
    if isinstance(data, list):
        return [dict_to_model(item) for item in data]

    class DynamicObject:
        def __init__(self, data: dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    setattr(self, key, dict_to_model(value))
                elif isinstance(value,
                                str):  # Восстанавливаем datetime из строки
                    try:
                        setattr(self, key, datetime.fromisoformat(value))
                    except (ValueError, TypeError):
                        setattr(self, key, value)
                else:
                    setattr(self, key, value)

    return DynamicObject(data)


def cached(key_template: str, ttl: int = 3600) -> Callable:
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = None
            try:
                # Генерация ключа (ваша оригинальная логика)
                format_kwargs = defaultdict(str, {
                    'user_id': kwargs.get("user_id") or (
                        args[1] if len(args) > 1 else None),
                    'product_id': kwargs.get("product_id") or (
                        args[2] if len(args) > 2 else None),
                    'category_id': kwargs.get("category_id") or (
                        args[3] if len(args) > 3 else None),
                    'page': kwargs.get("page") or (
                        args[4] if len(args) > 4 else None)
                })
                # Проверка обязательных параметров
                if not format_kwargs['page']:
                    logger.warning("Попытка кеширования с page=None")
                    return await func(*args,
                                      **kwargs)  # Пропускаем кеширование

                cache_key = key_template.format_map(format_kwargs).replace(
                    "::", ":")

                async with redis_cache.session() as redis:
                    # Проверка кеша
                    if cached_data := await redis.get(cache_key):
                        if cached_data == b'null':  # Сохраненный None
                            return None
                        return dict_to_model(orjson.loads(cached_data))

                    # Выполнение запроса, если нет в кеше
                    result = await func(*args, **kwargs)

                    logger.debug(f"Cache KEY: {cache_key}")
                    if cached_data:
                        logger.debug(f"Cache HIT: {cache_key}")
                    else:
                        logger.debug(f"Cache MISS: {cache_key}")

                    # Сериализация и сохранение
                    if result is None:
                        await redis.setex(cache_key, ttl, b'null')
                    else:
                        await redis.setex(
                            cache_key,
                            ttl,
                            orjson.dumps(
                                model_to_dict(result),
                                option=orjson.OPT_NAIVE_UTC
                                # Автоконвертация datetime в UTC
                            )
                        )
                    return result

            except Exception as e:
                logger.error(f"Cache error: {str(e)}", exc_info=True)
                return await func(*args, **kwargs)

        return wrapper

    return decorator
