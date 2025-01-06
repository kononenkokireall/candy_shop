# Обработчики корзины
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from ..keyboards import item_detail_kb


router = Router()

# --- Хранилище корзины в памяти ---
CART_STORAGE = {}

# --- Функция для получения корзины пользователя ---
def get_user_cart(user_id):
    """
    Возвращает корзину пользователя по его ID
    """
    return CART_STORAGE.setdefault(user_id, [])

# --- Добавление ковара в корзину ---
@router.message()
async def add_to_cart(message: Message, state: FSMContext):
    """
    Добавляет товар в корзину если пользователь указал ID товара
    """
    user_id = message.from_user.id
    user_data = await state.get_data()
    selected_category = user_data.get("selected_category")
    product_catalog = user_data.get("product_catalog")

    if selected_category and product_catalog:
        selected_item_id = message.text.strip()
        items = product_catalog.get(selected_category, {}).get("items", [])

        for item in items:
            if item["id"] == selected_item_id:
                user_cart = get_user_cart(user_id)
                user_cart.append(item)
                await message.answer(
                    f"Товар \"{item['name']}\" добавлен в корзину.",
                    reply_markup=item_detail_kb(),
                )
                return

    await message.answer("Товар с указаным ID не найден. Попробуйте еще раз.")

# --- Просмотр корзины ---
@router.message(Command(commands=['cart']))
async def view_cart(message: Message):
    """
    Отображает содержимое корзины пользователя
    """
    user_id = message.from_user.id
    user_cart = get_user_cart(user_id)

    if not user_cart:
        await message.answer("Ваша корзина пуста.")
    else:
        cart_items = "\n\n".join(
            [f"""Название: {item["name"]}\nЦена {
                item['price']} PLN""" for item in user_cart]
        )
        total_price = sum(item["price"] for item in user_cart)
        await message.answer(f"""Ваши товары: \n\n{cart_items}\n\nСумма к оплате: {total_price} PLN""", reply_markup=item_detail_kb(user_cart[0].get("category", ""))
                             )

# --- Очистка корзины ---
@router.callback_query(lambda callback: callback.data == "cart_clear")
async def clear_cart(callback_query: CallbackQuery):
    """
    Очищает корзину пользователя
    """
    user_id = callback_query.from_user.id
    CART_STORAGE[user_id] = []
    await callback_query.message.edit_text("Корзина успешно очищена.")

# --- Оформление заказа ---


@router.callback_query(lambda callback: callback.data == "cart_checkout")
async def checkout_cart(callback_query: CallbackQuery):
    """
    Завершает процесс оформления заказа
    """
    user_id = callback_query.from_user.id
    user_cart = get_user_cart(user_id)

    if not user_cart:
        await callback_query.message.edit_text("""Ваша корзина пуста. 
                                               Для оформления сделайте заказ""")
    else:
        total_price = sum(item["price"] for item in user_cart)
        CART_STORAGE[user_id] = []  # Очищение корзины после оформления
        await callback_query.message.edit_text(
            f"Спасибо за заказ!) Сумма к оплате: {total_price} PLN."
        )
