from aiogram import F, types
from aiogram.fsm.context import FSMContext

from handlers.admin_events.admin_main import admin_router
from states.states import OrderProcess


# Handler для изменения цены товара
@admin_router.message(OrderProcess.PRICE, F.text)
async def add_price(message: types.Message, state: FSMContext):
    if message.text == "." and OrderProcess.product_for_change:  # Проверяем, если пользователь хочет оставить старую цену
        await state.update_data(price=OrderProcess.product_for_change.price)
    else:
        try:
            float(message.text)  # Проверяем, что введенная цена является числом
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)  # Обновляем данные FSM
    await message.answer("Загрузите изображение товара")  # Переход к загрузке изображения
    await state.set_state(OrderProcess.ADD_IMAGES)


# Handler для некорректного ввода на шаге PRICE
@admin_router.message(OrderProcess.PRICE)
async def add_price2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите стоимость товара")
