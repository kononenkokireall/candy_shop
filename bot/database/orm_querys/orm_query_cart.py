######################## Работа с корзинами #######################################
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Cart


# Добавление товара в корзину
async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Добавляет товар в корзину пользователя. Если товар уже есть в корзине,
    увеличивает его количество.
    """
    query = (select(Cart)
             .where(Cart.user_id == user_id,
                               Cart.product_id == product_id)
             .options(joinedload(Cart.product)))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:  # Если товар уже в корзине, увеличиваем количество
        cart.quantity += 1
        await session.commit()
        return cart
    else:  # Иначе добавляем товар в корзину
        session.add(Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=1)
        )
        await session.commit()


# Получение корзины пользователя
async def orm_get_user_carts(session: AsyncSession, user_id):
    """
    Возвращает список всех товаров в корзине пользователя.
    """
    query = (select(Cart)
             .filter(Cart.user_id == user_id)
             .options(joinedload(Cart.product))
             )
    result = await session.execute(query)
    return result.scalars().all()


# Удаление товара из корзины
async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Удаляет товар из корзины по ID пользователя и ID товара.
    """
    query = (delete(Cart)
             .where(Cart.user_id == user_id,
                    Cart.product_id == product_id))
    await session.execute(query)
    await session.commit()


# Уменьшение количества товара в корзине
async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Уменьшает количество товара в корзине. Если количество становится 0, удаляет товар.
    """
    query = (select(Cart)
             .where(Cart.user_id == user_id,
                               Cart.product_id == product_id))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:  # Если товара нет, ничего не делаем
        return
    if cart.quantity > 1:  # Уменьшаем количество
        cart.quantity -= 1
        await session.commit()
        return True
    else:  # Если количество меньше 1, удаляем товар
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False
