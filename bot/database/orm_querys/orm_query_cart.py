import logging
from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Cart, User, Product

logger = logging.getLogger(__name__)


async def orm_add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    """Добавление товара в корзину с обработкой конфликтов"""
    try:
        # Проверка существования пользователя без блокировки
        user = await session.get(User, user_id)
        if not user:
            logger.error(f"[Cart] User {user_id} not found")
            return None

        # Проверка существования товара с загрузкой категории, но без блокировки
        product = await session.get(
            Product,
            product_id,
            options=[joinedload(Product.category)]
        )
        if not product or getattr(product, "is_deleted", False):
            logger.error(f"[Cart] Product {product_id} not found or deleted")
            return None

        # Upsert операция
        stmt = (
            insert(Cart)
            .values(
                user_id=user_id,
                product_id=product_id,
                quantity=1
            )
            .on_conflict_do_update(
                constraint="uix_user_product",
                set_={
                    "quantity": Cart.quantity + 1,
                    "updated": func.now()
                }
            )
            .returning(Cart)
        )

        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()

    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"[Cart] Ошибка добавления товара: {str(e)}",
                     exc_info=True)
        await session.rollback()
        return None


async def orm_get_user_carts(
        session: AsyncSession,
        user_id: int,
) -> Sequence[Cart]:
    """Получение корзины пользователя с полной информацией"""
    try:
        result = await session.execute(
            select(Cart)
            .options(
                joinedload(Cart.product).joinedload(Product.category)
            )
            .where(Cart.user_id == user_id)
            .order_by(Cart.created.desc())
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Error: {str(e)}")
        raise  # Пробрасываем ошибку, чтобы вызывающий код мог обработать


async def orm_add_product_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    """Увеличение количества товара в корзине"""
    try:
        # Поиск или блокировка записи
        cart_item = await session.scalar(
            select(Cart)
            .where(Cart.user_id == user_id, Cart.product_id == product_id)
            .with_for_update(skip_locked=True)
        )

        if cart_item:
            cart_item.quantity += 1
            cart_item.updated = func.now()
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=1,
                created=func.now(),
                updated=func.now()
            )
            session.add(cart_item)

        await session.commit()
        return cart_item

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(
            f"[Cart] Error при добавлении товара {product_id} для пользователя {user_id}: {str(e)}")
        raise


async def orm_reduce_product_in_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    """Уменьшение количества товара в корзине"""
    try:
        # Блокировка записи для конкурентного доступа с skip_locked
        cart_item = await session.scalar(
            select(Cart)
            .where(Cart.user_id == user_id, Cart.product_id == product_id)
            .with_for_update(skip_locked=True)
        )
        if not cart_item:
            return None

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            # quantity уже 1 — не уменьшаем дальше
            logger.info(
                f"[Cart] Quantity для товара {product_id} уже 1. Не уменьшаем.")

        cart_item.updated = func.now()
        await session.commit()
        return cart_item

    except SQLAlchemyError as e:
        logger.error(f"[Cart] Error: {str(e)}")
        raise  # Пробрасываем ошибку для обработки выше


async def orm_full_remove_from_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> bool:
    """Полное удаление товара из корзины"""
    try:
        result = await session.execute(
            delete(Cart).where(Cart.user_id == user_id)
            .where(Cart.user_id == user_id, Cart.product_id == product_id)
            .returning(Cart.id),
            execution_options={"synchronize_session": False}
        )
        deleted_id = result.scalar_one_or_none()
        await session.commit()
        return bool(deleted_id)

    except SQLAlchemyError as e:
        logger.error(f"[Cart] Error: {str(e)}")
        raise  # Пробрасываем ошибку для обработки выше
