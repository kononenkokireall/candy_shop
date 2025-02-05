from aiogram import F, types
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext

from handlers.admin_events.admin_main import admin_router
from states.states import OrderProcess


# Handler для возврата на шаг назад в FSM
@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state() # Получаем текущее состояние FSM

    if current_state == OrderProcess.NAME: # Проверяем, если пользователь уже на самом первом шаге
        await message.answer(
            'Предыдущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    # Перебираем все состояния FSM, чтобы установить предыдущее состояние
    for step in OrderProcess.__all_states__:
        if step.state == current_state:
            await state.set_state(previous) # Устанавливаем предыдущее состояние
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n"
                f"{OrderProcess.TEXTS[previous.state]}"
                # Выводим текст для прошлого шага
            )
            return
        previous = step