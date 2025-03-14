import logging
from typing import Optional, Sequence

from sqlalchemy import insert, select, delete, func
from sqlalchemy.dialects.postgresql import insert  # <-- Важное изменение
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Cart, User, Product

logger = logging.getLogger(__name__)



async def orm_add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    logger.info(f"Adding product {product_id} to cart for user {user_id}")

    try:
        async with session.begin():
            # Проверка существования пользователя
            user = await session.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Проверка существования товара
            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Product {product_id} not found")
                return None

            # Используем правильную конструкцию для UPSERT
            stmt = (
                insert(Cart)
                .values(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=1  # <-- Добавляем начальное значение
                )
                .on_conflict_do_update(
                    constraint='uix_user_product',
                    set_={
                        "quantity": Cart.quantity + 1,
                        "updated": func.now()  # <-- Обновляем метку времени
                    }
                )
                .returning(Cart)
            )

            result = await session.execute(stmt)
            cart_item = result.scalar_one()

            logger.info(f"Cart updated. New quantity: {cart_item.quantity}")
            return cart_item

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await session.rollback()
        return None
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        await session.rollback()
        return None

async def orm_get_user_carts(
        session: AsyncSession,
        user_id: int
) -> Sequence[Cart]:
    try:
        result = await session.execute(
            select(Cart)
            .options(joinedload(Cart.product))
            .where(Cart.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        return result.scalars().unique().all()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return []


async def orm_delete_from_cart(
        session: AsyncSession,
        user_id: int,
        product_id: Optional[int] = None
) -> bool:
    try:
        query = delete(Cart).where(Cart.user_id == user_id)
        if product_id:
            query = query.where(Cart.product_id == product_id)
            msg = f"product {product_id}"
        else:
            msg = "all products"

        result = await session.execute(query)

        if result.rowcount > 0:
            logger.info(f"Deleted {msg} from user {user_id}'s cart")
            return True

        logger.warning(f"No items deleted for user {user_id}")
        return False

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await session.rollback()
        return False


async def orm_reduce_product_in_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[bool]:
    logger.info(f"Reducing product {product_id} for user {user_id}")

    try:
        async with session.begin():
            cart_item = await session.scalar(
                select(Cart)
                .where(
                    Cart.user_id == user_id,
                    Cart.product_id == product_id
                )
                .with_for_update()
            )

            if not cart_item:
                logger.warning(f"No cart item found")
                return None

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                logger.info(f"New quantity: {cart_item.quantity}")
                return True
            else:
                await session.delete(cart_item)
                logger.info("Item removed from cart")
                return False

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await session.rollback()
        return None