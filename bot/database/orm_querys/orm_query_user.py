from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, exc
from typing import Dict, Any, Optional
import logging

from database.models import User  # Убедись, что импорт верный

logger = logging.getLogger(__name__)


# Добавляет или обновляет пользователя в базе данных (UPSERT операция).
def safe_username(username: Optional[str], user_id: int) -> str:
    """
    Возвращает непустой username без «@».
    Если username None/пустой — генерирует `id<user_id>`.
    """
    if username and username.strip():
        return username.lstrip("@")[:64]          # обрезаем по длине поля
    return f"id{user_id}"                         # запасной вариант


async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str = "Не указано",
    last_name: str = "Не указано",
    phone: Optional[str] = None,
    username: Optional[str] = None,               # ← новый аргумент
) -> Dict[str, Any]:
    """
    UPSERT пользователя. Всегда возвращает
    {'status': 'created'|'updated', 'details': {...}}  либо кидает исключение.
    """
    # ---------- валидация / нормализация ---------------------------------
    first_name = (first_name or "Не указано").strip()[:150]
    last_name  = (last_name or "Не указано").strip()[:150]
    phone      = phone.strip()[:13] if phone else None
    username   = safe_username(username, user_id)          # ← гарантировано не NULL

    # ---------- upsert ---------------------------------------------------
    stmt = (
        insert(User)
        .values(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            username=username,
            created=func.now(),
            updated=func.now(),
        )
        .on_conflict_do_update(
            index_elements=[User.user_id],
            set_={
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "username": username,
                "updated": func.now(),
            },
        )
        .returning(User.user_id, User.created, User.updated)
    )

    try:
        row = (await session.execute(stmt)).first()
        if not row:
            raise RuntimeError("UPSERT did not return row")

        is_new = row.created == row.updated
        status = "created" if is_new else "updated"
        logger.info(f"User {status}: {user_id}")

        return {
            "status": status,
            "details": {
                "user_id": row.user_id,
                "created": row.created,
                "updated": row.updated,
            },
        }

    except exc.IntegrityError as e:
        logger.error(f"[User {user_id}] integrity error: {e}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"[User {user_id}] DB error: {e}")
        raise