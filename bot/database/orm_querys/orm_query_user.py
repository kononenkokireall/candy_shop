##################### Работа с пользователями #####################################
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
        phone: Optional[str] = None
) -> Dict[str, Any]:
    result_info = {'status': 'error', 'details': None}

    try:
        insert_data = {
            'user_id': user_id,
            'first_name': first_name.strip()[:150],
            'last_name': last_name.strip()[:150],
            'phone': phone[:13].strip() if phone else None,
        }

        upsert_stmt = (
            insert(User)
            .values(**insert_data)
            .on_conflict_do_update(
                index_elements=['user_id'],
                set_={
                    'first_name': insert_data['first_name'],
                    'last_name': insert_data['last_name'],
                    'phone': insert_data['phone'],
                    'updated': func.now()
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
                    status='created' if is_new else 'updated',
                    details={
                        'user_id': row.user_id,
                        'created': row.created,
                        'updated': row.updated,
                    }
                )
                logger.info(f"User {'created' if is_new else 'updated'}: {user_id}")
            return result_info

    except exc.IntegrityError as e:
        logger.error(f"Integrity error: {str(e)}")
        result_info['details'] = str(e)
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        result_info['details'] = str(e)
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        result_info['details'] = str(e)

    return result_info
