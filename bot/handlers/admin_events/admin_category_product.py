from aiogram import F, types

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys_order.orm_query_create_order import orm_get_categories, orm_get_products
from handlers.admin_events.admin_main import admin_router
from keyboards.inline_main import get_callback_btn


# Handler для отображения ассортимента (категорий товаров)
@admin_router.message(F.text == 'Ассортимент')
async def admin_features(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session) # Получаем категории из базы данных
    btn = {category.name : f'category_{category.id}' for category in categories} # Генерируем кнопки с категориями
    await message.answer("Выберите категорию", reply_markup=get_callback_btn(btn=btn))


# Handler для отображения товаров из выбранной категории
@admin_router.callback_query(F.data.startswith('category_'))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split('_')[-1]# Получаем ID категории
    # Перебираем все товары из базы данных для данной категории
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.description}\n"
                    f"Стоимость: {round(product.price, 2)}",
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
