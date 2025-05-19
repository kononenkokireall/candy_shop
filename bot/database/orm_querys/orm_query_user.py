from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, exc
from typing import Dict, Any, Optional
import logging

from database.models import User  # Убедись, что импорт верный

logger = logging.getLogger(__name__)


# Добавляет или обновляет пользователя в базе данных (UPSERT операция).
async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str = "Не указано",
        last_name: str = "Не указано",
        phone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Добавляет или обновляет пользователя.

    Возвращает:
        dict: Словарь с ключами:
            - status (str): 'created', 'updated' или 'error'
            - details (dict | str | None): Дополнительная информация
    """
    result_info: Dict[str, Any] = {"status": "error", "details": None}

    # Валидация данных
    first_name = first_name.strip()[:150] if first_name else "Не указано"
    last_name = last_name.strip()[:150] if last_name else "Не указано"
    phone = phone[:13].strip() if phone else None

    # Подготовка данных для UPSERT
    insert_data = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "created": func.now(),
        "updated": func.now(),
    }

    # Операция UPSERT (вставка или обновление)
    upsert_stmt = (
        insert(User)
        .values(**insert_data)
        .on_conflict_do_update(
            index_elements=["user_id"],
            set_={
                "first_name": insert_data["first_name"],
                "last_name": insert_data["last_name"],
                "phone": insert_data["phone"],
                "updated": func.now(),  # `created` не обновляем
            }
        )
        .returning(User.user_id, User.created, User.updated)
    )
    try:
        # Проверяем, не находимся ли мы уже в транзакции
        if session.in_transaction():
            # Если уже в транзакции, выполняем только запрос
            result = await session.execute(upsert_stmt)
            row = result.first()
        else:
            # Если нет активной транзакции, создаем новую
                result = await session.execute(upsert_stmt)
                row = result.first()

        if row:
            is_new = row.created == row.updated
            result_info.update(
                status="created" if is_new else "updated",
                details={
                    "user_id": row.user_id,
                    "created": row.created,
                    "updated": row.updated
                },
            )
            logger.info(
                f"User {'created' if is_new else 'updated'}: {user_id}"
            )
    except exc.IntegrityError as e:
        logger.error(f"Integrity error while adding user {user_id}: {str(e)}")
        result_info["details"] = str(e)
        raise

    except exc.SQLAlchemyError as e:
        logger.error(f"Database error while adding user {user_id}: {str(e)}")
        result_info["details"] = str(e)
        raise

    except Exception as e:
        logger.exception(
            f"Unexpected error while adding user {user_id}: {str(e)}")
        result_info["details"] = str(e)
        raise

    return result_info