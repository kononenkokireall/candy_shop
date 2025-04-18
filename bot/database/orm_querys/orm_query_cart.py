import logging
from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cache.decorators import cached, set_cache
from cache.invalidator import CacheInvalidator
from database.models import Cart, User, Product

logger = logging.getLogger(__name__)
CART_TTL = 60  # Время жизни кэша корзины в секундах (1 минут)


async def _invalidate_cart_cache(user_id: int):
    """Инвалидация кэша корзины при изменениях"""
    await CacheInvalidator.invalidate([f"cart:{user_id}"])


async def orm_add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    """
    Добавление товара в корзину с обработкой конфликтов.
    Особенности:
    - Использует UPSERT (INSERT ON CONFLICT DO UPDATE)
    - Проверяет существование пользователя и товара
    - Автоматически увеличивает количество при повторном добавлении
    - Инвалидирует кэш корзины
    """
    logger.info(f"Adding product {product_id} to cart for user {user_id}")
    try:
        async with session.begin():  # Автоматический коммит/откат транзакции
            # Проверка существования пользователя
            user = await session.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # Проверка существования и активности товара
            product = await session.get(Product, product_id)
            if not product or getattr(product, "is_deleted", False):
                logger.error(f"Product {product_id} not found")
                return None

            # UPSERT-запрос с обработкой уникального ограничения
            stmt = (
                insert(Cart)
                .values(user_id=user_id, product_id=product_id, quantity=1)
                .on_conflict_do_update(
                    constraint="uix_user_product",
                    # Ожидает уникальный индекс (user_id, product_id)
                    set_={"quantity": Cart.quantity + 1, "updated": func.now()}
                )
                .returning(Cart)  # Возвращает обновленную/созданную запись
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one()

            await _invalidate_cart_cache(user_id)  # Сброс кэша
            await set_cache(
                key=f"cart:{user_id}",
                data=await orm_get_user_carts(session, user_id,
                                              _bypass_cache=True),
                ttl=CART_TTL,
                model=Cart
            )
            return cart_item
    except (IntegrityError, SQLAlchemyError) as e:
        logger.error(f"[Cart] Ошибка: {str(e)}")
        return None


@cached("cart:{user_id}",
        ttl=CART_TTL,
        model=Cart,
        cache_empty_results=True,
        empty_ttl=30
        )
async def orm_get_user_carts(
        session: AsyncSession,
        user_id: int,
        _bypass_cache: bool = False
) -> Sequence[
    Cart]:
    """
    Получение корзины пользователя с кэшированием.
    Особенности:
    - Использует selectinload для жадной загрузки связанных моделей
    - Кэширует результат с автоматическим ключом "cart:{user_id}"
    - Сортировка по времени добавления (новые первыми)
    """
    try:
        result = await session.execute(
            select(Cart)
            .options(
                selectinload(Cart.product)  # Жадная загрузка продукта
                .selectinload(Product.category)  # И его категории
            )
            .where(Cart.user_id == user_id)
            .order_by(Cart.created.desc())  # Сортировка по дате добавления
        )
        carts = result.scalars().all()
        return carts
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка получения корзины {user_id}: {str(e)}")
        return []


async def orm_reduce_product_in_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> Optional[Cart]:
    """
    Уменьшение количества товара в корзине.
    Особенности:
    - Использует row-level блокировку (with_for_update)
    - Полностью удаляет товар при количестве <= 1
    - Инвалидирует кэш после изменения
    """
    logger.info(f"[Cart] Уменьшение товара {product_id} для {user_id}")
    try:
        async with session.begin():
            # Блокировка строки для конкурентного доступа
            cart_item = await session.scalar(
                select(Cart)
                .where(Cart.user_id == user_id, Cart.product_id == product_id)
                .with_for_update(skip_locked=True)
                # Пропуск заблокированных строк
            )
            if not cart_item:
                return None

            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                session.add(cart_item)
            else:
                await session.delete(cart_item)  # Полное удаление при 1 шт

            await _invalidate_cart_cache(user_id)
            await set_cache(
                key=f"cart:{user_id}",
                data=await orm_get_user_carts(session, user_id,
                                              _bypass_cache=True),
                ttl=CART_TTL,
                model=Cart
            )
            return cart_item
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка изменения: {str(e)}")
        return None


async def orm_full_remove_from_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int
) -> bool:
    """
    Полное удаление товара из корзины.
    Особенности:
    - Использует bulk delete для эффективности
    - Возвращает статус операции (удалено/не найдено)
    - Инвалидирует кэш при успешном удалении
    """
    try:
        async with session.begin():
            result = await session.execute(
                delete(Cart)
                .where(Cart.user_id == user_id, Cart.product_id == product_id)
                .returning(Cart.id)  # Возврат ID для проверки успешности
            )
            if not result.scalar_one_or_none():
                return False

            await _invalidate_cart_cache(user_id)
            await set_cache(
                key=f"cart:{user_id}",
                data=await orm_get_user_carts(session, user_id,
                                              _bypass_cache=True),
                ttl=CART_TTL,
                model=Cart
            )

            return True
    except SQLAlchemyError as e:
        logger.error(f"[Cart] Ошибка удаления: {str(e)}")
        return False
