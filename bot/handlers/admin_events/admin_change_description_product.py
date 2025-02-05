from aiogram import F, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_get_categories
from handlers.admin_events.admin_main import admin_router
from keyboards.inline_main import get_callback_btn
from states.states import OrderProcess


# Handler для получения описания товара
@admin_router.message(OrderProcess.DESCRIPTION, F.text)
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    # Проверяем, если пользователь хочет оставить старое описание
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(description=OrderProcess.product_for_change.description)
    else:
        # Проверка минимальной длины описания
        if 4 >= len(message.text):
            await message.answer(
                "Слишком короткое описание. \n"
                "Введите заново"
            )
            return
        await state.update_data(description=message.text)  # Обновляем данные FSM

    # Генерация кнопок с категориями
    categories = await orm_get_categories(session)
    btn = {category.name: str(category.id) for category in categories}
    # Переход к выбору категории
    await message.answer("Выберите категорию", reply_markup=get_callback_btn(btn=btn))
    await state.set_state(OrderProcess.CATEGORY)


# Handler для некорректного ввода на шаге DESCRIPTION
@admin_router.message(OrderProcess.DESCRIPTION)
async def add_description2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")