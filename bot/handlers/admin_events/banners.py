# Добавляем/изменяем изображение в таблице
# (там уже есть записанные страницы по именам:
# main, catalog, cart(для пустой корзины), about, payment, shipping
from aiogram import types, F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_banner import orm_change_banner_image, \
    orm_get_info_pages
from database.orm_querys.orm_query_product import orm_add_product, \
    orm_update_product
from handlers.admin_events.admin_main import admin_router_root
from handlers.admin_events.base import ADMIN_KB
from states.states import OrderProcess, AddBanner

banners_router = Router(name="admin_banners")


@admin_router_root.message(AddBanner.IMAGE, F.photo)
async def add_banner(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
) -> None:
    if message.photo is None or len(message.photo) == 0:
        await message.answer("Отправьте фото баннера")
        return

    if message.caption is None:  # Исправление строки 346
        await message.answer("Укажите страницу для баннера")
        return

    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id, )
    await message.answer("Баннер добавлен/изменен.")
    await state.clear()


# Получение некорректного ввода
@admin_router_root.message(AddBanner.IMAGE)
async def add_banner2(message: types.Message) -> None:
    await message.answer("Отправьте фото баннера или отмена")


# Handler для добавления/изменения изображения товара
@admin_router_root.message(OrderProcess.ADD_IMAGES, or_f(F.photo,
                                                    F.casefold()))
async def add_image(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
) -> None:
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
        # Проверяем, если происходит изменение существующего товара
        if OrderProcess.product_for_change:
            # Обновляем товар
            await orm_update_product(session,
                                     OrderProcess.product_for_change.id, data)
        else:
            # Добавляем товар
            await orm_add_product(session, data)
        # Сообщение об успехе
        await message.answer("Товар добавлен/Изменен",
                             reply_markup=ADMIN_KB)
        # Сбрасываем состояние FSM
        await state.clear()

    # Обработка ошибок
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\n"
            f"Обратись к разработчику",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    # Сброс объекта изменения
    OrderProcess.product_for_change = None


# Handler для некорректного действия на шаге ADD_IMAGES
@admin_router_root.message(OrderProcess.ADD_IMAGES)
async def add_image2(message: types.Message) -> None:
    await message.answer("Отправьте фото пищи")

