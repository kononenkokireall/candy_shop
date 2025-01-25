from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_query import (
    orm_change_banner_image,
    orm_get_category,
    orm_get_info_pages,
    orm_add_product,
    orm_delete_product,
    orm_get_products,
    orm_get_product,
    orm_update_product)

from states import OrderProcess, AddBanner
from filters.chat_types import ChatTypeFilter, IsAdmin
from decimal import Decimal
from keyboards.reply import get_keyboard
from keyboards.inline import get_callback_btn

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())

ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Ассортимент",
    placeholder="Выберите действие",
    sizes=(2,),
)


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_category(session)
    btn = {category.name: f'category_{category.id}' for category in categories}
    await message.answer("Выберите категорию",
                         reply_markup=get_callback_btn(btn=btn))


@admin_router.callback_query(F.data.startswith('category_'))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split('_')[-1]
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                        </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btn(
                btn={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫")


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split('_')[-1]
    await orm_delete_product(session, int(product_id))
    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


# ----- FSM для загрузки и изменения баннеров -------

# Отправка перечня информационных страниц бота и переход в состояние отправки фото

@admin_router.message(StateFilter(None), F.text == "Добавить/Изменить баннер")
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\n"
                         f"В описании укажите для какой страницы: {', '.join(pages_names)}")
    await state.set_state(AddBanner.image)

    # Добавляем/изменяем изображение в таблице(внутри таблицы записанные страницы по именам:
    # main, catalog, cart(для пустой корзины), about payment, shipping


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы,"
                             f" например: {', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, image_id, for_page)
    await message.answer("Баннер добавлен/изменен.")
    await state.clear()


# Получение не корректного ввода
@admin_router.message(AddBanner.image)
async def error_data(message: types.Message):
    await message.answer("Отправьте фото баннера!")


# ------- FSM для добавления или изменения товаров админом ------

@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product(callback: types.CallbackQuery,
                         session: AsyncSession, state: FSMContext):
    product_id = callback.data.split('_')[-1]
    product_for_change = await orm_get_product(session, int(product_id))
    OrderProcess.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.name)


# Становимся в состояние ожидания ввода name
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderProcess.name)


# Handler отмены и сброса состояния должен быть всегда именно здесь,
# после того как только встали в состояние номер 1.
@admin_router.message(StateFilter('*'), Command("отмена"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if OrderProcess.product_for_change:
        OrderProcess.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Вернутся на шаг назад
@admin_router.message(StateFilter('*'), Command("назад"))
@admin_router.message(StateFilter('*'), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == OrderProcess.name:
        await message.answer('Предыдущего шага нет, введите название товара или нажмите "отмена" ')
        return
    previous = None
    for step in OrderProcess.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу\n"
                                 f" {OrderProcess.texts[previous.state]}")
            return
        previous = step


# Получаем данные для состояния registration и меняем состояние на description
@admin_router.message(OrderProcess.name, or_f(F.text, F.text.casefold()))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == '.' and OrderProcess.product_for_change:
        await state.update_data(name=OrderProcess.product_for_change.name)
    else:
        if  4 >= len(message.text) >= 100:
            await message.answer("Название товара не должно превышать 100 символов."
                                 "\n Введите заново")
            return

        await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(OrderProcess.description)


# Получение некорректных вводов для состояния name
@admin_router.message(OrderProcess.name)
async def error_data(message: types.Message):
    await message.answer("Вы ввели не корректные данные, введите текст названия товара.")


# Получаем данные для состояния description и переводим в состояние price
@admin_router.message(OrderProcess.description, F.text.casefold())
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == '.' and OrderProcess.product_for_change:
        await state.update_data(description=OrderProcess.product_for_change.description)
    else:
        if 4 >= len(message.text):
            await message.answer("Слишком короткое описание.\nВведите описание заново")
            return
        await state.update_data(description=message.text)

    categories = await orm_get_category(session)
    btn = {category_user.name: str(category_user.id) for category_user in categories}
    await message.answer("Введите категорию товара", reply_markup=get_callback_btn(btn=btn))
    await state.set_state(OrderProcess.category)


# Получение некорректных данных для состояния description
@admin_router.message(OrderProcess.description)
async def error_data(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


@admin_router.callback_query(OrderProcess.category)
async def change_category(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    if int(callback.data) in [category.id for category in await orm_get_category(session)]:
        await callback.answer()
        await state.update_data(category=int(callback.data))
        await callback.message.answer("Теперь введите цену товара.")
        await state.set_state(OrderProcess.price)
    else:
        await callback.message.answer("Выберите категорию из кнопок.")
        await callback.answer()


# # Получение всех некорректных действий, кроме нажатия на кнопку выбора категории.
# @admin_router.message(OrderProcess.category)
# async def error_change_category(message: types.Message, state: FSMContext):
#     await message.answer("Выберите категорию кнопок.")


# Получение данных для состояния price с переходом в состояние image
@admin_router.message(OrderProcess.price, F.text.casefold())
async def add_price(message: types.Message, state: FSMContext):
    if message.text == '.' and OrderProcess.product_for_change:
        await state.update_data(price=OrderProcess.product_for_change.price)
    else:
        try:
            price = Decimal(message.text)
            await state.update_data(price=price)
        except Exception as e:
            await message.answer(f"Введите корректное значение цены. {e}")
            return

        await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара")
    await state.set_state(OrderProcess.add_images)


# # Получение некорректных данных ввода для состояния price
# @admin_router.message(OrderProcess.price)
# async def error_data_image(message: types.Message, state: FSMContext):
#     await message.answer("Введены не допустимые данные, введите стоимость товара!")


# Получение данных add_image с последующим выходом из состояния
@admin_router.message(OrderProcess.add_images, or_f(F.photo, F.text.casefold()))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == '.' and OrderProcess.product_for_change:
        await state.update_data(image=OrderProcess.product_for_change.image)
    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото пищи!")
        return
    data = await state.get_data()

    try:
        if OrderProcess.product_for_change:
            await orm_update_product(session, OrderProcess.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен/Изменить товар", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратитесь к разработчику", reply_markup=ADMIN_KB
        )
        await state.clear()

    OrderProcess.product_for_change = None
