# Handler для выбора категории через Callback
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_product import orm_get_products
from handlers.admin_events.admin_main import admin_router_root
from keyboards.inline_main import get_callback_btn
from states.states import OrderProcess

category_router = Router(name="admin_category")

@admin_router_root.callback_query(OrderProcess.CATEGORY)
async def category_choice(
        callback: types.CallbackQuery,
        state: FSMContext,
        session: AsyncSession
) -> None:
    # Проверка наличия данных и их типа
    if callback.data is None or not callback.data.isdigit():
        await callback.answer("❌ Некорректные данные")
        return

    # Получаем список существующих категорий
    categories = await orm_get_categories(session)

    # Преобразуем ID категорий в целые числа
    valid_category_ids = {category.id for category in categories}

    # Проверяем валидность выбранной категории
    if int(callback.data) in valid_category_ids:
        await callback.answer()  # Подтверждаем выбор
        await state.update_data(category=callback.data)  # Сохраняем категорию

        await callback.message.answer('Теперь введите цену товара.')
        await state.set_state(OrderProcess.PRICE)
    else:
        await callback.message.answer('Выберите категорию из кнопок.')
        await callback.answer()  # Отправляем пустой ответ для закрытия всплывания


# Handler для некорректного ввода на шаге CATEGORY
@admin_router_root.message(OrderProcess.CATEGORY)
async def category_choice2(message: types.Message) -> None:
    await message.answer("'Выберите категорию из кнопок.'")


# Handler для отображения товаров из выбранной категории
@admin_router_root.callback_query(F.data.startswith('category_'))
async def starring_at_product(
        callback: types.CallbackQuery,
        session: AsyncSession
) -> None:
    if callback.data is None:
        await callback.answer("❌ Ошибка данных")
        return

    parts = callback.data.split('_')
    category_id = parts[-1] if len(parts) > 1 else None

    if not category_id or not category_id.isdigit():
        await callback.answer("⚠️ Неверный формат ID категории")
        return

    products = await orm_get_products(session, int(category_id))
    if not products:
        await callback.answer("📭 Товары в категории отсутствуют")
        return

    for product in products:
        if callback.message and product.image:
            await callback.message.answer_photo(
                product.image,
                caption=f"📦 {product.name}\n💵 Цена: {product.price},\n"
                        f"📊 Остаток: <b>{product.stock}</b> шт.",
                reply_markup=get_callback_btn(btn={
                    "🗑 Удалить": f"delete_{product.id}",
                    "✏️ Изменить": f"change_{product.id}",
                }, sizes=(2,)))

            if callback.message:
                await callback.message.answer("✅ Список товаров обновлен")
            await callback.answer()
