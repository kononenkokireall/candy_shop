"""
Этот модуль содержит обработчики для работы с каталогом товаров.
"""
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from data import PRODUCT_CATALOG
from states import OrderProcess
from keyboards import catalog_kb, pay_methods_kb, item_detail_kb

router = Router()

# Обработчик нажатия на кнопку каталога

@ router.callback_query(lambda callback: callback.data.startswith("catalog_"))
async def user_catalog(callback: CallbackQuery):
    """
    Проверяет, существует ли выбранная категория в 
    Обрабатывает выбор категории из каталога и выводит список товаров.
    """
    category_key = callback.data
    if category_key in PRODUCT_CATALOG:
        item = PRODUCT_CATALOG[category_key]
        await callback.message.edit_text(
            f"""<b>{item['name']}<b>\n\n{
                item['description']}<b>\nPrice{item['price']}""",
            reply_markup=item_detail_kb(category_key)
        )
    else:
        await callback.message.answer("Извините, выбранная категория временно отсутствует.")


@router.callback_query(lambda callback_query: callback_query.data.startswith("category_"))
async def handle_category_selection(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор категории и отображает список товаров с их ID, именами,
    описаниями и ценами.
    """
    category_key = callback_query.data.split("_")[1]
    category = PRODUCT_CATALOG.get(category_key)

    if category:
        await state.update_data(selected_category=category_key)
        items = "\n\n".join([
            f"""ID: {item['id']}\nНазвание: {item['name']}\nОписание: {
                item['description']}\nЦена: {item['price']} PLN."""
            for item in category["items"]
        ])
        await callback_query.message.answer(f"""Категория: {category['name']}
                                            \n\n{items}\n\n
                                            Для добавления товара в корзину напишите его ID.""")
    else:
        await callback_query.message.answer("Выбранная категория не найдена.")


# Обработчик нажатия на кнопку (Добавить товар в корзину)
@ router.callback_query(lambda callback: callback.data.startswith("add_to_cart_"))
async def handle_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """
    Извлекает информацию о выбранном товаре из toy_catalog по ключу,
    указанному в callback.data.
    Сохраняет его в состоянии пользователя (FSMContext).
    """
    category_key = callback.data.replace("add_to_cart_", "")
    item = PRODUCT_CATALOG.get(category_key)

    if item:
        # Сохраняем товар в контексте
        user_data = await state.get_data()
        cart = user_data.get("cart", [])
        cart.append(item)
        await state.update_data(cart=cart)
        await callback.message.answer(
            f"""Товар {
                item['name']}, добавлен в корзину.\n Желаете продолжить покупки?""",
            reply_markup=catalog_kb()
        )
    else:
        await callback.message.answer("Ошибка добавления товара в корзину.")
# Обработчик команды для просмотра корзины


@ router.message(lambda message: message.text.lower() == "ваша корзина")
async def user_view_cart(message: Message, state: FSMContext):
    """
    Извлекает данные корзины из состояния пользователя.
    """
    user_data = await state.get_data()
    cart = user_data.get('cart', [])

    if cart:
        cart_text = "Ваши товары в корзине: \n\n" + "\n".join(
            [f"{item['name']} - {item['price']}" for item in cart]
        )
        await message.answer(cart_text)
    else:
        await message.answer("Ваша корзина пуста.")

# Обработчик нажатия кнопки(Выбрать способ оплаты)


@ router.callback_query(lambda callback: callback.data == "choose_payment")
async def user_choose_payment(callback: CallbackQuery, state: FSMContext):
    """
    Устанавливает состояние пользователя как OrderProcess.Payment.
    """
    await state.set_state(OrderProcess.Payment)
    await callback.message.edit_text(
        "Выберите способ оплаты: ", reply_markup=pay_methods_kb()
    )
