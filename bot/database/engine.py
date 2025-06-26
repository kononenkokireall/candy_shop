"""
Async SQLAlchemy engine & session factory (refactored, v2).

* Нет logging.basicConfig — конфигурация делается в точке входа.
* Параметры пула совместимы с asyncpg; меняются через ENV.
* create_schema / seed_initial_data — разделены (DDL ↔ DML).
* Добавлены алиасы session_maker / create_db / drop_db для
  обратной совместимости со «старым» кодом.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from utilit.config import database_url
from database.models import Base

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
ECHO_SQL = bool(os.getenv("DEBUG_SQL", ""))
engine = create_async_engine(
    database_url,
    echo=ECHO_SQL,
    connect_args={
        "command_timeout": int(os.getenv("DB_COMMAND_TIMEOUT", "30"))},
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

# —––– ALIАS для старых импортов –––––––––––––––––––––––––––––––––––––––––––
# (если в проекте ещё есть `from database.engine import session_maker`)
session_maker = SessionFactory  # noqa: N816


# ---------------------------------------------------------------------------
# Context manager — одна транзакция на запрос/апдейт
# ---------------------------------------------------------------------------
@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    async with SessionFactory() as session:
        async with session.begin():
            yield session


# ---------------------------------------------------------------------------
# Schema helpers (CI / DEV)
# ---------------------------------------------------------------------------
async def create_schema() -> None:
    """Создаёт все таблицы согласно metadata."""
    logger.info("Creating DB schema…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Schema ready.")


async def drop_schema() -> None:
    """Удаляет все таблицы — DEV-утилита, не вызывайте в проде!"""
    logger.warning("Dropping DB schema…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("Schema dropped.")


# Aliases для старого кода
create_db = create_schema  # noqa: N816
drop_db = drop_schema  # noqa: N816


# ---------------------------------------------------------------------------
# Seed helpers (заполняем справочники)
# ---------------------------------------------------------------------------
async def seed_initial_data() -> None:
    from common.texts_for_db import categories_goods, \
        description_for_info_pages
    from database.orm_querys.orm_query_category import orm_create_categories
    from database.orm_querys.orm_query_banner import orm_add_banner_description

    logger.info("Seeding reference data…")
    try:
        async with SessionFactory() as session:
            await orm_create_categories(session, categories_goods)
            await orm_add_banner_description(session,
                                             description_for_info_pages)
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Seed failed → rollback")
        raise
    logger.info("Seed completed.")


# ---------------------------------------------------------------------------
# Shutdown helper
# ---------------------------------------------------------------------------
async def dispose() -> None:
    """Закрыть пул соединений (вызывайте при остановке приложения)."""
    logger.debug("Disposing engine…")
    await engine.dispose()
    logger.debug("Engine disposed.")
