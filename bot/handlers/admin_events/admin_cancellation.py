from aiogram import F, types
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext

from handlers.admin_events.admin_main import admin_router, ADMIN_KB
from states.states import OrderProcess


# Handler отмены и сброса состояния
@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()  # Получаем текущее состояние машины состояний
    if current_state is None: # Если состояния нет, завершаем выполнение
        return
    if OrderProcess.product_for_change: # Сбрасываем объект изменения, если он существует
        OrderProcess.product_for_change = None
    await state.clear() # Сбрасываем все состояния FSM
    await message.answer("Действия отменены", reply_markup=ADMIN_KB) # Возвращаем пользователя в главное меню
