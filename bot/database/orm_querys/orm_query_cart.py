import logging
import pickle
from typing import List, Optional, Any, Sequence

from sqlalchemy import select, delete, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cache.decorators import cached
from cache.invalidator import CacheInvalidator
from database.models import Cart, User, Product

logger = logging.getLogger(__name__)
CART_TTL = 300  # 5 минут в секундах


async def _invalidate_cart_cache(user_id: int):
    await CacheInvalidator.invalidate([
        f"cart:{user_id}",
        f"user:{user_id}:orders"
    ])


async def orm_add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    logger.info(f"Adding product {product_id} to cart for user {user_id}")
    try:
        async with session.begin():
            user = await session.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Product {product_id} not found")
                return None

            stmt = (
                insert(Cart)
                .values(user_id=user_id, product_id=product_id, quantity=1)
                .on_conflict_do_update(
                    constraint="uix_user_product",
                    set_={"quantity": Cart.quantity + 1, "updated": func.now()}
                )
                .returning(Cart)
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one()

            await _invalidate_cart_cache(user_id)
            return cart_item
    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"[Cart] Ошибка: {str(e)}")
        return None


@cached("cart:{user_id}", ttl=CART_TTL)
async def orm_get_user_carts(session: AsyncSession, user_id: int) -> Sequence[
                                                                         Cart] | \
                                                                     list[Any]:
    try:
        result = await session.execute(
            select(Cart)
            .options(selectinload(Cart.product).selectinload(Product.category))
            .where(Cart.user_id == user_id)
            .order_by(Cart.created.desc())
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка получения корзины {user_id}: {str(e)}")
        return []


async def orm_reduce_product_in_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    logger.info(f"[Cart] Уменьшение товара {product_id} для {user_id}")
    try:
        async with session.begin():
            cart_item = await session.scalar(
                select(Cart)
                .where(Cart.user_id == user_id, Cart.product_id == product_id)
                .with_for_update(skip_locked=True)
            )
            if not cart_item:
                return None

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                session.add(cart_item)
            else:
                await session.delete(cart_item)

            await _invalidate_cart_cache(user_id)
            return cart_item
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка изменения: {str(e)}")
        return None


async def orm_full_remove_from_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> bool:
    try:
        async with session.begin():
            result = await session.execute(
                delete(Cart)
                .where(Cart.user_id == user_id, Cart.product_id == product_id)
                .returning(Cart.id)
            )
            if not result.scalar_one_or_none():
                return False

            await _invalidate_cart_cache(user_id)
            return True
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка удаления: {str(e)}")
        return False
