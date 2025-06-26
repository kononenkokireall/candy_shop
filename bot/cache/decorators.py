"""
@cached – декоратор для Redis-кэша.

* Пользуется новым get_redis() из cache.redis
* Логирование без повторного basicConfig
"""
from __future__ import annotations

import datetime
import decimal
import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union

import orjson
from sqlalchemy.orm import InstrumentedAttribute

from cache.redis import get_redis  # NEW

logger = logging.getLogger(__name__)
cache_logger = logging.getLogger("cache")
cache_logger.setLevel(logging.DEBUG)
cache_logger.addHandler(
    logging.FileHandler("cache.log", mode="a", encoding="utf-8")
)


# ---------------------------------------------------------------------------
# Utils – model ↔ dict
# ---------------------------------------------------------------------------
def model_to_dict(obj: Any) -> Union[Dict, List]:
    if isinstance(obj, list):
        return [model_to_dict(i) for i in obj]

    if hasattr(obj, "__table__"):
        result: Dict[str, Any] = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, decimal.Decimal):
                value = float(value)
            elif isinstance(value, (datetime.datetime, datetime.date)):
                value = value.isoformat()
            result[column.name] = value

        # only loaded relations
        for attr, value in getattr(obj, "__dict__", {}).items():
            if isinstance(value, list):
                result[attr] = [model_to_dict(i) for i in value if
                                hasattr(i, "__table__")]
            elif hasattr(value, "__table__"):
                result[attr] = model_to_dict(value)
        return result
    return obj


def dict_to_model(data: Union[Dict, List], model: Type) -> Any:
    if isinstance(data, list):
        return [dict_to_model(item, model) for item in data]

    obj = model()
    for key, value in data.items():
        if not hasattr(model, key):
            continue
        if isinstance(value, dict):
            attr = getattr(model, key, None)
            if isinstance(attr, InstrumentedAttribute) and hasattr(
                    attr.property, "mapper"):
                setattr(obj, key,
                        dict_to_model(value, attr.property.mapper.class_))
        elif isinstance(value, list) and hasattr(getattr(model, key, None),
                                                 "property"):
            related_model = getattr(model, key).property.mapper.class_
            setattr(obj, key, [dict_to_model(i, related_model) for i in value])
        else:
            setattr(obj, key, value)
    return obj


# ---------------------------------------------------------------------------
# Cached decorator
# ---------------------------------------------------------------------------
def cached(
        key_template: str,
        ttl: int = 3600,
        model: Optional[Type] = None,
        defaults: Optional[Dict[str, Any]] = None,
        cache_empty_results: bool = False,
        empty_ttl: int = 60,
) -> Callable:
    defaults = defaults or {}

    def decorator(func: Callable[..., Any]):
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.pop("_bypass_cache", False):
                cache_logger.debug("[Cache BYPASS] %s", key_template)
                return await func(*args, **kwargs)

            # формируем ключ
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            full_kwargs = {**defaults, **bound.arguments}
            key = key_template.format(**full_kwargs)

            try:
                # ── GET
                async with get_redis() as redis:
                    raw = await redis.get(key)
                if raw is not None:
                    cache_logger.debug("[Cache HIT] %s", key)
                    data = orjson.loads(raw)
                    if data is None:
                        return None
                    if model:
                        return (
                            [dict_to_model(i, model) for i in data]
                            if isinstance(data, list)
                            else dict_to_model(data, model)
                        )
                    return data

                # ── MISS
                result = await func(*args, **kwargs)

                if result is not None and (result or cache_empty_results):
                    ser = (
                        orjson.dumps([model_to_dict(i) for i in result])
                        if isinstance(result, list)
                        else orjson.dumps(model_to_dict(result))
                    )
                    ttl_use = ttl if result else empty_ttl
                    async with get_redis() as redis:
                        await redis.setex(key, ttl_use, ser)
                    cache_logger.debug("[Cache SET] %s ttl=%s", key, ttl_use)
                return result

            except Exception:  # pragma: no cover
                cache_logger.exception("[Cache ERROR] %s", key_template)
                return await func(*args, **kwargs)

        return wrapper

    return decorator
