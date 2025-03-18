##################### Работа с пользователями ################################
import logging
from typing import Optional, Dict, Any

from sqlalchemy import func, exc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

logger = logging.getLogger(__name__)


async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str = "Не указано",
        last_name: str = "Не указано",
        phone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Возвращает:
        dict: Словарь с ключами:
            - status (str): 'created', 'updated' или 'error'
            - details (str | dict | None): Дополнительная информация
    """
    result_info: dict[str, Any] = {
        "status": "error",
        "details": None,  # Теперь может быть dict, str или None
    }

    try:
        # Валидация данных (можно вынести в отдельный метод)
        first_name = first_name.strip()[:150] if first_name else "Не указано"
        last_name = last_name.strip()[:150] if last_name else "Не указано"
        phone = phone[:13].strip() if phone else None

        # Явная проверка существования пользователя
        existing_user = await session.get(User, user_id)
        is_new = existing_user is None

        # Подготовка данных для UPSERT
        insert_data = {
            "user_id": user_id,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "updated": func.now(),  # Гарантированное обновление времени
        }

        # Если пользователь существует, добавляем created только для новых
        if is_new:
            insert_data["created"] = func.now()

        upsert_stmt = (
            insert(User)
            .values(**insert_data)
            .on_conflict_do_update(index_elements=["user_id"],
                                   set_=insert_data)
            .returning(User.user_id, User.created, User.updated)
        )

        async with session.begin():
            result = await session.execute(upsert_stmt)
            row = result.first()

            if row:
                result_info.update(
                    status="created" if is_new else "updated",
                    details={
                        "user_id": row.user_id,
                        "created": row.created,
                        "updated": row.updated,
                    },
                )
                logger.info(
                    f"User {'created' if is_new else 'updated'}: {user_id}")
            return result_info

    except exc.IntegrityError as e:
        logger.error(f"Integrity error: {str(e)}")
        result_info["details"] = str(e)
        await session.rollback()  # Явный откат
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        result_info["details"] = str(e)
        await session.rollback()
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        result_info["details"] = str(e)
        await session.rollback()

    return result_info
