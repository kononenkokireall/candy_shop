from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_add_user, orm_add_to_cart
from keyboards.inline_main import MenuCallBack


# Функция добавления товара в корзину
async def add_to_cart(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession
):
    user_local = callback.from_user  # Получаем информацию о пользователе
    # Добавляем пользователя в базу данных
    await orm_add_user(
        session,
        user_id=user_local.id,
        first_name=user_local.first_name,
        last_name=user_local.last_name,
        phone=None,
    )
    # Добавляем товар в корзину
    await orm_add_to_cart(session, user_id=user_local.id, product_id=callback_data.product_id)
    # Отправляем уведомление пользователю
    await callback.answer("Товар добавлен в корзину!")