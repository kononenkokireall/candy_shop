import logging
from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.dialects.postgresql import insert
# Используется для поддержки UPSERT-операций
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Cart, User, Product

# Инициализируем логгер для данного модуля
logger = logging.getLogger(__name__)


async def orm_add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> None:
    """
    Добавляет товар в корзину пользователя с использованием UPSERT.
    Если для комбинации (user_id, product_id) уже существует запись,
    увеличивается количество (quantity) на 1,

     иначе создается новая запись с quantity=1.

    Аргументы:
      - session: Асинхронная сессия SQLAlchemy.
      - user_id: Идентификатор пользователя.
      - product_id: Идентификатор товара.

    Возвращает:
      - Объект Cart, обновленный или созданный, либо None при ошибке.
    """
    logger.info(f"Adding product {product_id} to cart for user {user_id}")

    try:
        async with session.begin():
            # Проверяем, существует ли пользователь
            user = await session.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Проверяем, существует ли товар
            product = await session.get(Product, product_id)
            if not product:
                logger.error(f"Product {product_id} not found")
                return None

            # Формируем выражение UPSERT: вставляем новую запись,
            # а при конфликте по ограничению 'uix_user_product'
            # увеличиваем quantity на 1 и обновляем метку времени.
            stmt = (
                insert(Cart)
                .values(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=1,  # Начальное значение для нового товара
                )
                .on_conflict_do_update(
                    constraint="uix_user_product",
                    set_={
                        "quantity": Cart.quantity + 1,
                        "updated": func.now(),  # Обновляем временную метку
                    },
                )
                .returning(Cart)
            )

            result = await session.execute(stmt)
            cart_item = result.scalar_one()

            logger.info(f"Cart updated. New quantity: {cart_item.quantity}")
            return None

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await session.rollback()
        return None
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        await session.rollback()
        return None


async def orm_get_user_carts(
        session: AsyncSession, user_id: int) -> Sequence[Cart]:
    """
    Получает список товаров в корзине для указанного пользователя.
    При этом загружаются связанные объекты Product
     для каждого элемента корзины.

    Аргументы:
      - session: Асинхронная сессия SQLAlchemy.
      - user_id: Идентификатор пользователя.

    Возвращает:
      - Список объектов Cart. При ошибке возвращается пустой список.
    """
    try:
        result = await session.execute(
            select(Cart)
            .options(
                joinedload(Cart.product)
            )  # Пред загрузка данных о товаре для каждого элемента корзины
            .where(Cart.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        return result.scalars().unique().all()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return []


async def orm_delete_from_cart(
        session: AsyncSession, user_id: int, product_id: Optional[int] = None
) -> bool:
    """
    Удаляет товар(ы) из корзины пользователя.
    Если указан product_id, удаляется только соответствующая запись,
    иначе удаляются все товары для данного пользователя.

    Аргументы:
      - session: Асинхронная сессия SQLAlchemy.
      - user_id: Идентификатор пользователя.
      - product_id: (Опционально) Идентификатор товара для удаления.

    Возвращает:
      - True, если были удалены записи; False,
       если не было записей для удаления.
    """
    try:
        # Формируем запрос на удаление записей из корзины
        # для указанного пользователя
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
        session: AsyncSession, user_id: int, product_id: int
) -> Optional[bool]:
    """
    Уменьшает количество товара в корзине пользователя на 1.
    Если количество товара становится равным 1, удаляет запись из корзины.

    Аргументы:
      - session: Асинхронная сессия SQLAlchemy.
      - user_id: Идентификатор пользователя.
      - product_id: Идентификатор товара.

    Возвращает:
      - True, если количество товара уменьшено,
      — False, если товар удален из корзины,
      — None, если товар не найден или произошла ошибка.
    """
    logger.info(f"Reducing product {product_id} for user {user_id}")

    try:
        async with session.begin():
            # Используем with_for_update
            # для блокировки записи до завершения операции,
            # чтобы предотвратить конкурентное обновление.
            cart_item = await session.scalar(
                select(Cart)
                .where(Cart.user_id == user_id,
                       Cart.product_id == product_id)
                .with_for_update()
            )

            if not cart_item:
                logger.warning("No cart item found")
                return None

            # Если количество больше 1, уменьшаем его на 1.
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                logger.info(f"New quantity: {cart_item.quantity}")
                return True
            else:
                # Если количество равно 1, удаляем запись из корзины.
                await session.delete(cart_item)
                logger.info("Item removed from cart")
                return False

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        await session.rollback()
        return None
