from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_add_product,
    orm_get_products,
    orm_delete_product,
    orm_get_product,
    orm_update_product)

from states import OrderProcess
from filters.chat_types import ChatTypeFilter, IsAdmin
from decimal import Decimal
from keyboards.reply import get_keyboard
from keyboards.inline import get_callback_btn


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

filter_states = OrderProcess()

ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Ассортимент",
    placeholder="Выберите действие",
    sizes=(2,),
)


@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Ассортимент")
async def starring_at_product(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image, caption=f"<strong>{product.name}</strong>\n{product.description}\n"
                                   f"Стоимость: {product.price, 2}",
            reply_markup=get_callback_btn(
                btn={
                    'Удалить': f'delete_{product.id}',
                    'Изменить': f'change_{product.id}'
                }
            )
        )
    await message.answer("ОК, вот список товаров")

@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split('_')[-1]
    await orm_delete_product(session, int(product_id))
    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product(callback: types.CallbackQuery,
                         session: AsyncSession, state: FSMContext):
    product_id = callback.data.split('_')[-1]
    product_for_change = await orm_get_product(session, int(product_id))
    filter_states.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(filter_states.name)



# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(filter_states.name)


# Handler отмены и сброса состояния должен быть всегда именно здесь,
# после того как только встали в состояние номер 1.
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return
    if filter_states.product_for_change:
        filter_states.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Вернутся на шаг назад
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == filter_states.name:
        await message.answer('Предыдущего шага нет, введите название товара или нажмите "отмена" ')
        return
    previous = None
    for step in filter_states.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу\n"
                                 f" {filter_states.texts[previous.state]}")
            return
        previous = step
    await message.answer(f"ок, вы вернулись к прошлому шагу")


# Получаем данные для состояния registration и меняем состояние на description
@admin_router.message(filter_states.name, or_f(F.text, F.text.casefold()))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(name=filter_states.product_for_change.name)
    else:
        if len(message.text) >= 100:
            await message.answer("Название товара не должно превышать 100 символов.\n Введите заново")
            return

        await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(filter_states.description)

@admin_router.message(filter_states.name)
async def error_data(message: types.Message):
    await message.answer("Вы ввели не корректные данные, введите текст названия товара.")


# Получаем данные для состояния description и переводим в состояние price
@admin_router.message(filter_states.description, or_f(F.text, F.text.casefold()))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(description=filter_states.product_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введите стоимость товара")
    await state.set_state(filter_states.price)

@admin_router.message(filter_states.description)
async def error_data(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


# Получение данных для состояния price для перехода в состояние add_image
@admin_router.message(filter_states.price, or_f(F.text, F.text.casefold()))
async def add_price(message: types.Message, state: FSMContext):
    if message.text == '.':
        await state.update_data(price=filter_states.product_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара")
    await state.set_state(filter_states.add_images)


# Получение данных add_image с последующим выходом из состояния #TODO
@admin_router.message(filter_states.add_images, or_f( F.photo, F.text.casefold()))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):

    if message.text and message.text == '.':
        await state.update_data(image=filter_states.product_for_change.image)
    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()

    try:
        if filter_states.product_for_change:
            await orm_update_product(session, filter_states.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратитесь к разработчику", reply_markup=ADMIN_KB
        )
        await state.clear()

    filter_states.product_for_change = None