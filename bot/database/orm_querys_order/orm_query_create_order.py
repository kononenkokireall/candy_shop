import logging
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exc

from cache.invalidator import CacheInvalidator
from database.models import Order
from database.orm_querys_order.orm_query_add_order_items import \
    orm_add_order_items

logger = logging.getLogger(__name__)

# Функция Создает новый заказ в базе данных
async def orm_create_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        status: str = "pending",
) -> Order:
    """
    Создает новый заказ в базе данных

    Параметры:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        total_price: Общая сумма заказа
        address: Адрес доставки (опционально)
        phone: Контактный телефон (опционально)
        status: Статус заказа (по умолчанию "pending")

    Возвращает:
        Order: Созданный объект заказа

    Исключения:
        SQLAlchemyError: При ошибках работы с БД
    """
    logger.info(f"Создание заказа для пользователя {user_id}")

    try:
        # Валидация основных параметров
        if total_price <= 0:
            raise ValueError("Сумма заказа должна быть больше нуля")

        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Некорректный ID пользователя")

        # Создание объекта заказа
        order = Order(
            user_id=user_id,
            total_price=round(total_price, 2),
            status=status,
            address=address.strip() if address else None,
            phone=phone.strip() if phone else None,
        )

        session.add(order)
        await session.flush()
        logger.debug(f"Заказ создан с ID {order.id}")
        return order

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка БД при создании заказа: {str(e)}")
        await session.rollback()
        raise
    except Exception as e:
        logger.error(f"Ошибка валидации: {str(e)}")
        await session.rollback()
        raise

# Функция Добавляет товары в транзакции
async def orm_add_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: List[Dict],
        address: Optional[str] = None,
        phone: Optional[str] = None,
        status: str = "pending",
) -> Order:
    """
    Создает заказ и добавляет товары в транзакции

    Параметры:
        session: Асинхронная сессия БД
        user_id: ID пользователя
        total_price: Общая сумма заказа
        items: Список товаров для добавления
        address: Адрес доставки (опционально)
        phone: Контактный телефон (опционально)
        status: Статус заказа

    Возвращает:
        Order: Созданный объект заказа

    Исключения:
        RuntimeError: При ошибках создания заказа
    """
    logger.info(f"Оформление заказа для пользователя {user_id}")

    try:
        async with session.begin():
            # Создание основного заказа
            order = await orm_create_order(
                session=session,
                user_id=user_id,
                total_price=total_price,
                address=address,
                phone=phone,
                status=status,
            )

            # Добавление товаров
            logger.debug(f"Добавление {len(items)} товаров в заказ {order.id}")
            await orm_add_order_items(session=session, order_id=order.id,
                                      items=items)

            # Валидация общей суммы
            if abs(order.total_price - total_price) > 0.01:
                raise ValueError("Расхождение в общей сумме заказа")
            await CacheInvalidator.invalidate([f"orders:user:{user_id}"])
            logger.info(f"Заказ {order.id} успешно оформлен")
            return order

    except exc.SQLAlchemyError as e:
        logger.critical(f"Критическая ошибка БД: {str(e)}", exc_info=True)
        await session.rollback()
        raise RuntimeError("Ошибка сохранения заказа") from e
    except ValueError as e:
        logger.error(f"Ошибка валидации данных: {str(e)}")
        await session.rollback()
        raise RuntimeError("Некорректные данные заказа") from e
    except Exception as e:
        logger.exception("Неожиданная ошибка при создании заказа")
        await session.rollback()
        raise RuntimeError("Системная ошибка") from e
