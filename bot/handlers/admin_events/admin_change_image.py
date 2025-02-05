from aiogram import F, types
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_update_product, orm_add_product
from handlers.admin_events.admin_main import admin_router, ADMIN_KB
from states.states import OrderProcess


# Handler для изменения изображения товара
@admin_router.message(OrderProcess.ADD_IMAGES, or_f(F.photo, F.casefold()))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    # Проверяем, если пользователь хочет оставить старое изображение
    if message.text and message.text == "." and OrderProcess.product_for_change:
        await state.update_data(image=OrderProcess.product_for_change.image)

    elif message.photo:  # Проверяем, что пользователь отправил фото
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото пищи")  # Сообщение об ошибке
        return

    data = await state.get_data()  # Получаем все данные FSM
    try:
        if OrderProcess.product_for_change:  # Проверяем, если происходит изменение существующего товара
            await orm_update_product(session, OrderProcess.product_for_change.id, data)  # Обновляем товар
        else:
            await orm_add_product(session, data)  # Добавляем товар
        await message.answer("Товар добавлен или изменен", reply_markup=ADMIN_KB)  # Сообщение об успехе
        await state.clear()  # Сбрасываем состояние FSM

    except Exception as e:  # Обработка ошибок
        await message.answer(
            f"Ошибка: \n{str(e)}\n"
            f"Обратись к разработчику",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    OrderProcess.product_for_change = None  # Сброс объекта изменения


# Handler для некорректного действия на шаге ADD_IMAGES
@admin_router.message(OrderProcess.ADD_IMAGES)
async def add_image2(message: types.Message):
    await message.answer("Отправьте фото пищи")
