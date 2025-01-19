from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext


from filters.chat_types import ChatTypeFilter, IsAdmin
from keyboards.reply import get_keyboard
from states import OrderProcess


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

filter_states = OrderProcess()

ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Изменить товар",
    "Удалить товар",
    "Я так, просто посмотреть зашел",
    placeholder="Выберите действие",
    sizes=(2, 1, 1),
)


@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Я так, просто посмотреть зашел")
async def starring_at_product(message: types.Message):
    await message.answer("ОК, вот список товаров")


@admin_router.message(F.text == "Изменить товар")
async def change_product(message: types.Message):
    await message.answer("ОК, вот список товаров")


@admin_router.message(F.text == "Удалить товар")
async def delete_product(message: types.Message):
    await message.answer("Выберите товар(ы) для удаления")


#Код ниже для машины состояний (FSM)

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
@admin_router.message(filter_states.name, F.text)
async def add_name(message: types.Message, state: FSMContext):

    await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(filter_states.description)

@admin_router.message(filter_states.name)
async def error_data(message: types.Message):
    await message.answer("Вы ввели не корректные данные, введите текст названия товара.")


# Получаем данные для состояния description и переводим в состояние price
@admin_router.message(filter_states.description, F.text)
async def add_description(message: types.Message, state: FSMContext):

    await state.update_data(description=message.text)
    await message.answer("Введите стоимость товара")
    await state.set_state(filter_states.payment)


# Получение данных для состояния price для перехода в состояние add_image
@admin_router.message(filter_states.payment, F.text)
async def add_price(message: types.Message, state: FSMContext):

    await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара")
    await state.set_state(filter_states.add_images)


# Получение данных add_image с последующим выходом из состояния
@admin_router.message(filter_states.add_images, F.photo)
async def add_image(message: types.Message, state: FSMContext):

    await state.update_data(image=message.photo[-1].file_id)
    await message.answer("Товар добавлен", reply_markup=ADMIN_KB)
    data = await state.get_data()
    await message.answer(str(data))
    await state.clear()