##################### Работа с пользователями #####################################
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

# Настройка лога
logger = logging.getLogger(__name__)


# Добавление пользователя в базу
async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
):
    """
    Добавляет нового пользователя в базу данных, если его там еще нет.
    """
    logger.info(
        f"Попытка добавления пользователя: user_id={user_id},"
        f" first_name={first_name},"
        f" last_name={last_name}, phone={phone}")

    try:
        query = select(User).where(User.user_id == user_id)  # Проверяем, существует ли пользователь
        result = await session.execute(query)

        if result.first() is None:  # Если пользователь не найден, добавляем
            session.add(
                User(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone
                )
            )
            await session.commit()
            logger.info(f"Пользователь {user_id} успешно добавлен в базу")
        else:
            logger.warning(f"Пользователь {user_id} уже существует в базе")

    except Exception as e:
        await session.rollback()
        logger.exception(f"Ошибка при добавлении пользователя {user_id}: {str(e)}")
        raise
