################# Микро FSM для загрузки/изменения баннеров ############################
from aiogram import F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_get_info_pages, orm_change_banner_image
from handlers.admin_events.admin_main import admin_router
from states.states import AddBanner


# Handler для отправки перечня информационных страниц и входа в состояние загрузки изображения
@admin_router.message(StateFilter(None), F.text == 'Добавить или изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)] # Получаем список страниц
    await message.answer(f"Отправьте фото баннера.\n"
                         f"В описании укажите для какой страницы:\n"
                         f"{', '.join(pages_names)}")
    await state.set_state(AddBanner.IMAGE) # Устанавливаем состояние-загрузку изображения


# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, catalog, cart(для пустой корзины), about, payment, shipping
@admin_router.message(AddBanner.IMAGE, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    admin_link = message.caption.split("|")[-1].strip() # Получаем ссылку администратора
    image_id = message.photo[-1].file_id # ID изображения
    for_page = message.caption.strip() # Название страницы
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names: # Проверка валидности названия страницы
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    # Сохраняем изменения в базе данных
    await orm_change_banner_image(session, for_page, image_id, admin_link=admin_link)
    await message.answer("Баннер добавлен или изменен.")
    await state.clear()


# Handler для обработки некорректного ввода во время загрузки баннера
@admin_router.message(AddBanner.IMAGE)
async def add_banner2(message: types.Message):
    await message.answer("Отправьте фото баннера или отмена")

