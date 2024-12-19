# Обработчики каталога товаров
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from keyboards import catalog_keyboard, payment_methods_keyboard, item_detali_keyboard
from states import OrderProcess

router = Router()

# Данные каталога товаров
# Это пример товара который нужно доработать
PRODUCT_CATALOG = {
    "lollipops": {
        "name": "Canabis Lollipops",
        "items": [
            {
                "id": "101",
                "name": "Hemperium's Original",
                "description": """Оригинальные леденцы с каннабисом от Hemperium
                        Леденцы с каннабисом от Hemperium стали первыми победителями
                        Кубка каннабиса HIGH TIMES. Еще в 1999 году Hemperium
                        с гордостью выпустил свой первый продукт собственной
                        разработки из каннабиса: оригинальные леденцы
                        Cannabis Lollipops, изготовленные из 100% натурального масла каннабиса.
                        Они имели огромный успех и выиграли High Times Cannabis Cup в Амстердаме
                        в номинации «Лучший продукт», а затем еще один первый приз
                        на Haarlem Hemp Awards несколько недель спустя.
                        Теперь, спустя более двух десятилетий после их появления,
                        они по-прежнему, если не больше, являются одними из самых популярных
                        в мире лакомств из каннабиса.
                        Присоединяйтесь к нам, чтобы отпраздновать это знаменательное событие
                        выпуском эксклюзивного юбилейного издания!""",
                "price": 19},
            {
                "id": "102",
                "name": "Bubblegum x Candy Kush",
                "description": """Еще в 1999 году Hemperium с гордостью выпустила свой первый
                          продукт собственной разработки из каннабиса:
                          АБСОЛЮТНО оригинальные леденцы из каннабиса, изготовленные
                          из 100% настоящего европейского масла каннабиса.
                          Основатель компании Крис получил массу комплиментов
                          за свое новое творение. Поэтому он решил выставить
                          их на премию на престижном High Times Cannabis Cup,
                          который ежегодно проводится в Амстердаме. В ноябре
                          того же года, когда новый веб-сайт был закончен как
                          раз вовремя, компания представила свои леденцы из
                          каннабиса на церемонии награждения. Это оказалось
                          огромным успехом, потому что, к удивлению Криса,
                          Hemperium выиграл награду за лучший продукт из
                          конопли, а несколько недель спустя эффектно последовала
                          еще одна первая премия на премии Haarlem Hemp Awards.""",
                "price": 19,
            },
            {
                "id": "103",
                "name": "Northern Lights x Pineapple Express",
                "description": """Вместе с отмеченным наградами производителем конфет
                          из каннабиса Hemperium, Dr. Greenlove производит
                          качественные леденцы из каннабиса с широким спектром
                          захватывающих вкусов. Hemperium вышел на сцену, когда
                          их полностью оригинальные леденцы из каннабиса
                          выиграли первую в истории награду за продукт на
                          High Times Cannabis Cup в Амстердаме. Dr. Greenlove очень
                          гордится сотрудничеством с этим легендарным производителем
                          и первопроходцем и представляет вам совершенно новую линейку
                          этих классических каннабисов. Это, например,
                          Northern Lights x Pineapple Express,
                          один из многих вкусов в коллекции.
                """,
                "price": 19,
            }
        ]
    },
    "accessories": {
        "name": "thimbles",
        "items": [
            {
                "id": "201",
                "name": "orange_thimbles",
                "description": "description",
                "prince": "000"
            }
        ]
    }
}
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
            reply_markup=item_detali_keyboard(category_key)
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
                item['description']}\nЦена: {item['price']} ZL."""
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
            reply_markup=catalog_keyboard()
        )
    else:
        await callback.message.answer("Ошибка добавления товара в корзину.")
# Обработчик команды для просмотра корзины


@ router.message(lambda message: message.text.lower() == "Ваша корзина")
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
        "Выберите способ оплаты: ", reply_markup=payment_methods_keyboard
    )
