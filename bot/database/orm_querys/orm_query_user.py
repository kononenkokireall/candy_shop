##################### Работа с пользователями #####################################
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


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
    query = (select(User)
             .where(User.user_id == user_id))  # Проверяем, существует ли пользователь
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