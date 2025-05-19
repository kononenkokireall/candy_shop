import logging
from typing import Sequence

from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Order

logger = logging.getLogger(__name__)


# Функция Получает список заказов пользователя с пагинацией
async def orm_get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Order]:
    """
    Получает список заказов пользователя с пагинацией

    Параметры:
        session (AsyncSession): Асинхронная сессия БД
        user_id (int): Идентификатор пользователя
        limit (int): Максимальное количество заказов (по умолчанию 100)
        offset (int): Смещение выборки (по умолчанию 0)

    Возвращает:
        List[Order]: Список заказов с пред_загруженными позициями
        Пустой список если заказов не найдено

    Исключения:
        ValueError: При некорректном user_id
        SQLAlchemyError: При ошибках выполнения запроса
    """
    logger.info(
        f"Запрос заказов пользователя {user_id} [limit={limit},"
        f" offset={offset}]"
    )

    try:
        # Валидация входных параметров
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Некорректный идентификатор пользователя")

        if limit < 1 or limit > 1000:
            raise ValueError("Лимит должен быть в диапазоне 1-1000")

        # Формирование запроса
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                # Более эффективная загрузка для коллекций
                selectinload(Order.items)
            )
            .order_by(Order.created.desc())
            .limit(limit)
            .offset(offset)
        )

        # Выполнение запроса
        result = await session.execute(query)
        orders = result.scalars().all()

        # Логирование результатов
        if orders:
            logger.debug(f"Найдено {len(orders)} заказов для пользователя"
                         f" {user_id}")
        else:
            logger.info(f"Заказы для пользователя {user_id} не найдены")

        return orders

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка БД при получении заказов: {str(e)}",
                     exc_info=True)
        await session.rollback()
        raise
    except ValueError as e:
        logger.warning(f"Некорректные параметры запроса: {str(e)}")
        raise
    except Exception as e:
        logger.exception("Неожиданная ошибка при обработке запроса")
        await session.rollback()
        raise RuntimeError("Ошибка получения заказов") from e
