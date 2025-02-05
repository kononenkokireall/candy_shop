from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_get_categories
from handlers.admin_events.admin_main import admin_router
from states.states import OrderProcess


# Handler для выбора категории через Callback
@admin_router.callback_query(OrderProcess.CATEGORY)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if int(callback.data) in [category.id for category in
                              await orm_get_categories(session)]:  # Проверяем валидность выбранной категории
        await callback.answer()  # Подтверждаем выбор
        await state.update_data(category=callback.data)  # Сохраняем выбранную категорию в данные FSM
        await callback.message.answer('Теперь введите цену товара.')  # Переходим к следующему шагу
        await state.set_state(OrderProcess.PRICE)
    else:
        await callback.message.answer('Выберите категорию из кнопок.')  # Сообщение об ошибке
        await callback.answer()


# Handler для некорректного ввода на шаге CATEGORY
@admin_router.message(OrderProcess.CATEGORY)
async def category_choice2(message: types.Message):
    await message.answer("'Выберите категорию из кнопок.'")