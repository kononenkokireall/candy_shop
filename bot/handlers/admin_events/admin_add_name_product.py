######################### FSM для добавления/изменения товаров админом ###################
from aiogram import F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_get_product
from handlers.admin_events.admin_main import admin_router
from states.states import OrderProcess


# Handler для изменения товара (вход в состояние name)
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))
    # Получаем товар для изменения
    OrderProcess.product_for_change = product_for_change
    # Просим администратора ввести название товара
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.NAME)


# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.NAME)
