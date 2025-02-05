from aiogram import F, types
from aiogram.fsm.context import FSMContext

from handlers.admin_events.admin_main import admin_router
from states.states import OrderProcess


# Handler для введения названия товара.
# Получаем данные для состояния name и потом меняем состояние на DESCRIPTION
@admin_router.message(OrderProcess.NAME, F.text)
async def add_name(message: types.Message, state: FSMContext):
    # Проверяем, если пользователь хочет оставить старое название
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(name=OrderProcess.product_for_change.name)
        # Обновляем данные FSM
    else:
        # Здесь можно сделать какую либо дополнительную проверку
        # и выйти из handler не меняя состояние с отправкой соответствующего сообщения
        # например:
        # Проверка длины введенного названия
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\n"
                "или быть менее 5 ти символов. \n"
                "Введите заново"
            )
            return

        await state.update_data(name=message.text) # Обновляем данные FSM
    await message.answer("Введите описание товара") # Переходим к следующему шагу
    await state.set_state(OrderProcess.DESCRIPTION)

# Handler для некорректного ввода на шаге NAME
@admin_router.message(OrderProcess.NAME)
async def add_name2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст названия товара")