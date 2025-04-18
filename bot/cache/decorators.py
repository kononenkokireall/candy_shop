import datetime
import decimal
import functools
import logging
from typing import Any, Callable, Union, Dict, List, Optional, Type

import orjson
from sqlalchemy.orm import InstrumentedAttribute

from cache.redis import redis_cache

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

# Специальный логгер для кэша
cache_logger = logging.getLogger("cache")
cache_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("cache.log", mode="a", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
cache_logger.addHandler(file_handler)


def model_to_dict(obj: Any) -> Union[Dict, List]:
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]

    if hasattr(obj, '__table__'):
        result = {}
        # Сериализуем только колонки таблицы
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, decimal.Decimal):
                value = float(value)
            elif isinstance(value, (datetime.datetime, datetime.date)):
                value = value.isoformat()
            result[column.name] = value

        # Обрабатываем только загруженные отношения
        if hasattr(obj, '__dict__'):
            for attr_name, value in obj.__dict__.items():
                if isinstance(value, list):
                    # Если это список загруженных связанных объектов
                    result[attr_name] = [model_to_dict(i) for i in value if
                                         hasattr(i, '__table__')]
                elif hasattr(value, '__table__'):
                    result[attr_name] = model_to_dict(value)

        return result

    return obj


def dict_to_model(data: Union[Dict, List], model: Any) -> Any:
    if isinstance(data, list):
        return [dict_to_model(item, model) for item in data]

    obj = model()
    for key, value in data.items():
        if isinstance(value, dict):
            attr = getattr(model, key, None)
            if isinstance(attr, InstrumentedAttribute) and hasattr(
                    attr.property, "mapper"):
                related_model = attr.property.mapper.class_
                setattr(obj, key, dict_to_model(value, related_model))
        elif isinstance(value, list) and hasattr(getattr(model, key, None),
                                                 'property'):
            attr = getattr(model, key).property
            if hasattr(attr, "mapper"):
                related_model = attr.mapper.class_
                setattr(obj, key,
                        [dict_to_model(i, related_model) for i in value])
        else:
            setattr(obj, key, value)
    return obj


def cached(
        key_template: str,
        ttl: int = 3600,
        model: Optional[Type] = None,
        defaults: Optional[Dict] = None,
        cache_empty_results: bool = False,
        empty_ttl: int = 60,
) -> Callable:
    """
    Кэширование результата асинхронной функции с использованием Redis.
    key_template: шаблон ключа, поддерживает переменные как в f-строках,
    например: "cart:{user_id}"
    ttl: время жизни кэша в секундах
    model: модель SQLAlchemy (для сериализации и десериализации)
    cache_empty_results: кэшировать ли пустой результат (например, [])
    empty_ttl: TTL для пустых результатов
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.pop("_bypass_cache", False):
                cache_logger.debug(
                    f"[Cache BYPASS] key_template={key_template} kwargs={kwargs}")
                return await func(*args, **kwargs)

            try:
                key = key_template.format(**kwargs)
                async with redis_cache.session() as redis:
                    cached_data = await redis.get(key)
                    if cached_data:
                        cache_logger.debug(f"[Cache HIT] key={key}")
                        if model:
                            data = orjson.loads(cached_data)
                            if isinstance(data, list):
                                return [model(**item) for item in data]
                            return model(**data)
                        return orjson.loads(cached_data)

                result = await func(*args, **kwargs)

                if result or cache_empty_results:
                    data_to_cache = (
                        orjson.dumps([model_to_dict(obj) for obj in result])
                        if isinstance(result, list)
                        else orjson.dumps(model_to_dict(result))
                    )
                    ttl_to_use = ttl if result else empty_ttl
                    async with redis_cache.session() as redis:
                        await redis.setex(key, ttl_to_use, data_to_cache)
                    cache_logger.debug(
                        f"[Cache SET] key={key} ttl={ttl_to_use}")

                return result
            except Exception as e:
                cache_logger.error(
                    f"[Cache ERROR] key={key_template} error={e}")
                return await func(*args, **kwargs)

        return wrapper

    return decorator


async def set_cache(
        key: str,
        data: Any,
        ttl: int = 60,
        model: Optional[Type] = None
):
    """
    Прямое сохранение значения в кэш Redis.
    key — строка ключа, например: "cart:123"
    data — данные (модель или список моделей SQLAlchemy)
    ttl — время жизни
    model — модель, которую использовать для сериализации
    """
    try:
        if data is None:
            return

        serialized = (
            b"null" if data is None
            else orjson.dumps([
                                  model_to_dict(obj) for obj in data
                              ] if isinstance(data, list) else model_to_dict(
                data))
        )
        async with redis_cache.session() as redis:
            await redis.setex(key, ttl, serialized)
        cache_logger.debug(f"[CACHE SET] key={key}, ttl={ttl}")
    except Exception as e:
        cache_logger.error(f"[CACHE ERROR] Failed to set: {e}")
