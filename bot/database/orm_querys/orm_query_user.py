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

    try:
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

        async with session.begin():
            result = await session.execute(upsert_stmt)
            row = result.first()

            if row:
                is_new = row.created == row.updated
                result_info.update(
                    status="created" if is_new else "updated",
                    details={"user_id": row.user_id, "created": row.created,
                             "updated": row.updated},
                )
                logger.info(
                    f"User {'created' if is_new else 'updated'}: {user_id}")

        return result_info  # Возвращаем результат ТОЛЬКО если транзакция успешна

    except exc.IntegrityError as e:
        await session.rollback()
        logger.error(f"Integrity error: {str(e)}")
        result_info["details"] = str(e)
    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {str(e)}")
        result_info["details"] = str(e)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Unexpected error: {str(e)}")
        result_info["details"] = str(e)

    return result_info  # Теперь гарантировано возвращает ответ в случае ошибки
