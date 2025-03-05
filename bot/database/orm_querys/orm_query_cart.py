import logging
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Cart

# Настройка логгер
logger = logging.getLogger(__name__)

######################## Работа с корзинами #######################################

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Добавляет товар в корзину пользователя. Если товар уже есть в корзине,
    увеличивает его количество.
    """
    logger.info(f"Добавление товара {product_id} в корзину пользователя {user_id}")

    query = (select(Cart)
             .where(Cart.user_id == user_id, Cart.product_id == product_id)
             .options(joinedload(Cart.product)))
    cart = await session.execute(query)
    cart = cart.scalar()

    if cart:  # Если товар уже в корзине, увеличиваем количество
        cart.quantity += 1
        await session.commit()
        logger.info(f"Количество товара {product_id} в корзине пользователя {user_id} увеличено до {cart.quantity}")
        return cart
    else:  # Иначе добавляем товар в корзину
        new_cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        session.add(new_cart_item)
        await session.commit()
        logger.info(f"Товар {product_id} добавлен в корзину пользователя {user_id}")
        return new_cart_item


async def orm_get_user_carts(session: AsyncSession, user_id: int):
    """
    Возвращает список всех товаров в корзине пользователя.
    """
    logger.info(f"Запрос корзины пользователя {user_id}")

    query = (select(Cart)
             .filter(Cart.user_id == user_id)
             .options(joinedload(Cart.product)))
    result = await session.execute(query)
    carts = result.scalars().all()

    logger.info(f"Найдено {len(carts)} товаров в корзине пользователя {user_id}")
    return carts


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: Optional[int] = None):
    """
    Удаляет товар из корзины по ID пользователя и ID товара.
    """
    logger.info(f"Удаление товара {product_id} из корзины пользователя {user_id}")

    # Проверяем, есть ли товар в корзине
    query_check = select(Cart).where(Cart.user_id == user_id)
    if product_id is not None:
        query_check = query_check.where(Cart.product_id == product_id)

    existing_items = await session.execute(query_check)
    existing_items = existing_items.scalars().all()

    if not existing_items:
        logger.warning(f"Товар {product_id} не найден в корзине пользователя {user_id}")
        return

    # Если товар найден, удаляем
    query_delete = delete(Cart).where(Cart.user_id == user_id)
    if product_id is not None:
        query_delete = query_delete.where(Cart.product_id == product_id)

    await session.execute(query_delete)
    await session.commit()

    if product_id:
        logger.info(f"Товар {product_id} удален из корзины пользователя {user_id}")
    else:
        logger.info(f"Все товары удалены из корзины пользователя {user_id}")


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Уменьшает количество товара в корзине. Если количество становится 0, удаляет товар.
    """
    logger.info(f"Уменьшение количества товара {product_id} в корзине пользователя {user_id}")

    query = (select(Cart)
             .where(Cart.user_id == user_id, Cart.product_id == product_id))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        logger.warning(f"Товар {product_id} отсутствует в корзине пользователя {user_id}")
        return

    if cart.quantity > 1:  # Уменьшаем количество
        cart.quantity -= 1
        await session.commit()
        logger.info(f"Количество товара {product_id} уменьшено до {cart.quantity} в корзине пользователя {user_id}")
        return True
    else:  # Если количество 1, удаляем товар
        await orm_delete_from_cart(session, user_id, product_id)
        logger.info(f"Товар {product_id} полностью удален из корзины пользователя {user_id}")
        return False
