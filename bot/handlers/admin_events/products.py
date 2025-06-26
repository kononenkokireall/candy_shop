# Handler для изменения цены товара
from typing import Optional

from aiogram import F, types, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_product import orm_get_product
from handlers.admin_events.admin_main import admin_router_root
from keyboards.inline_main import get_callback_btn
from states.states import OrderProcess

products_router = Router(name="admin_products")

@admin_router_root.message(OrderProcess.PRICE, F.text)
async def add_price(
        message: types.Message,
        state: FSMContext
) -> None:

    text = message.text or ""
    text = text.replace(",", ".")

    if message.text is None:  # Проверка на None
        await message.answer("Введите цену товара")
        return

    # Проверяем, если пользователь хочет оставить старую цену
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(price=OrderProcess.product_for_change.price)
    else:
        try:
            # Проверяем, что введенная цена является числом
            price_val = float(text)
            if price_val <= 0:
                raise ValueError
        except ValueError:
            await message.answer("Введите корректную цену (число > 0)")
            return

        # Обновляем данные FSM
        await state.update_data(price=price_val)

        await message.answer("Укажите количество (остаток (шт.) >0)")
        await state.set_state(OrderProcess.QUANTITY)


@admin_router_root.message(OrderProcess.PRICE)
async def add_price_invalid(message: types.Message) -> None:
    await message.answer("Введите цену числом (например, 199.99) "
                         "или «.» чтобы оставить прежнюю цену.")


@admin_router_root.message(OrderProcess.QUANTITY, F.text)
async def add_quantity(
            message: types.Message,
            state: FSMContext,
    ) -> None:
        """
        Шаг QUANTITY: ждём целое положительное число.
        Поддерживаем «.» для сохранения прежнего количества.
        По успеху – просим фотографию и переходим в ADD_IMAGES.
        """
        text = (message.text or "").strip()

        # ── «оставить как есть» ───────────────────────────────────────────────
        if text == "." and OrderProcess.product_for_change:
            await state.update_data(
                quantity=OrderProcess.product_for_change.quantity
                if hasattr(OrderProcess.product_for_change, "quantity")
                else 1  # fallback, если нет такого поля
            )
        else:
            # ── валидация ─────────────────────────────────────────────────────
            if not text.isdigit() or int(text) <= 0:
                await message.answer("Введите количество целым числом (≥ 1)")
                return

            await state.update_data(quantity=int(text))

        # Переход к загрузке изображения
        await message.answer("Загрузите изображение товара")
        await state.set_state(OrderProcess.ADD_IMAGES)


@admin_router_root.message(OrderProcess.QUANTITY)
async def add_quantity_invalid(message: types.Message) -> None:
    await message.answer("Введите количество целым числом (≥ 1) "
                         "или «.» чтобы оставить прежнее количество.")

# Handler для изменения названия товара (вход в состояние name)
@admin_router_root.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
        callback: types.CallbackQuery,
        state: FSMContext,
        session: AsyncSession
) -> None:
    # Проверка данных callback
    if callback.data is None:
        await callback.answer("❌ Ошибка данных")
        return

    # Безопасное разделение данных
    parts = callback.data.split("_")
    product_id = parts[-1] if len(parts) > 1 else None

    if not product_id or not product_id.isdigit():
        await callback.answer("⚠️ Неверный формат ID")
        return

    product: Optional[Product] = await orm_get_product(session,
                                                       int(product_id))
    if product is None:
        OrderProcess.product_for_change = product
        await callback.answer("🔍 Товар не найден")
        return

    if callback.message:
        await callback.message.answer(
            "✏️ Введите новое название товара:",
            reply_markup=types.ReplyKeyboardRemove()
        )
    await state.set_state(OrderProcess.NAME)


# Handler для введения изменения названия товара.
# Получаем данные для состояния name и потом меняем состояние на DESCRIPTION
@admin_router_root.message(OrderProcess.NAME, F.text)
async def add_name(
        message: types.Message,
        state: FSMContext
) -> None:
    if message.text is None:  # Добавляем проверку на None
        await message.answer("Введите название товара")
        return

    # Проверяем, если пользователь хочет оставить старое название
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(name=OrderProcess.product_for_change.name)
        # Обновляем данные FSM
    else:
        # Здесь можно сделать какую либо дополнительную проверку
        # и выйти из handler не меняя состояние
        # с отправкой соответствующего сообщения
        # например:
        # Проверка длины введенного названия
        if len(message.text) < 5 or len(message.text) > 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\n"
                "или быть менее 5 ти символов. \n"
                "Введите заново"
            )
            return

        # Обновляем данные FSM
        await state.update_data(name=message.text)
    # Переходим к следующему шагу
    await message.answer("Введите описание товара")
    await state.set_state(OrderProcess.DESCRIPTION)


# Handler для некорректного ввода на шаге NAME
@admin_router_root.message(OrderProcess.NAME)
async def add_name2(message: types.Message) -> None:
    await message.answer(
        "Вы ввели не допустимые данные, введите текст названия товара")


# Handler для получения описания товара
@admin_router_root.message(OrderProcess.DESCRIPTION, F.text)
async def add_description(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
) -> None:
    if message.text is None:
        await message.answer("Введите описание товара")
        return
    # Проверяем, если пользователь хочет оставить старое описание
    if message.text == "." and OrderProcess.product_for_change:
        await state.update_data(
            description=OrderProcess.product_for_change.description)
    else:
        # Проверка минимальной длины описания
        if len(message.text) < 5:
            await message.answer(
                "Слишком короткое описание. \n"
                "Введите заново"
            )
            return
        await state.update_data(
            description=message.text)  # Обновляем данные FSM

    # Генерация кнопок с категориями
    categories = await orm_get_categories(session)
    btn = {
        category.name: str(category.id)  # Исправлен доступ к атрибутам
        for category in categories
    }
    # Переход к выбору категории
    await message.answer("Выберите категорию",
                         reply_markup=get_callback_btn(btn=btn))
    await state.set_state(OrderProcess.CATEGORY)


# Handler для некорректного ввода на шаге DESCRIPTION
@admin_router_root.message(OrderProcess.DESCRIPTION)
async def add_description2(message: types.Message) -> None:
    await message.answer(
        "Вы ввели не допустимые данные, введите текст описания товара")
