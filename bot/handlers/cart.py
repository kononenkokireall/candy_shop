# Обработчики корзины
import logging
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards import create_item_detail_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
                    # Формат сообщений
logger = logging.getLogger(__name__)

router = Router()

# --- Хранилище корзины в памяти ---
CART_STORAGE = {}

# --- Функция для получения корзины пользователя ---
def get_user_cart(user_id):
    """Возвращает корзину пользователя по его ID"""
    if not isinstance(user_id, int): # Проверка того что id корректный
        logger.error(f"Некорректный user_id: {user_id}.")
        return []
    logger.debug(f"Получение корзины для пользователя {user_id}...")
    return CART_STORAGE.setdefault(user_id, [])


# --- Служебная функция для подсчета итоговой суммы корзины ---
def calculate_cart_total(cart_items):
    try:
        total = sum(float(item.get("price", 0)) for item in cart_items)
        logger.debug(f"Итоговая сумма для корзины: {total}")
        return total
    except (TypeError, ValueError) as e:
        logger.error(f"Ошибка при расчете итоговой суммы: {str(e)}")
        return 0.00


# --- Добавление ковара в корзину ---
@router.message()
async def add_to_cart(message: Message, state: FSMContext):
    """Добавляет товар в корзину если пользователь указал ID товара"""
    user_id = message.from_user.id

    if not isinstance(user_id, int): # Проверка корректности user_id
        logger.warning(f"user_id отсутствует при добавлении в корзину.")
        await message.answer("Произошла ошибка при обработке вашего запроса.")
        return

    logger.info(f"Пользователь ({user_id}) пытается добавить товар в корзину.")
    try:
        user_data = await state.get_data()

        # Получение данных о категории и каталоге
        selected_category = user_data.get("selected_category")
        product_catalog = user_data.get("product_catalog")

        if not selected_category or not product_catalog:
            logger.error(f"У пользователя ({user_id}) отсутствубт необходимые "
                         f"данные в FSMContext.")
            await message.answer("Произошла ошибка при полученни данных."
                                 " Попробуйте еще раз.")
            return

        # Обработка ввода пользователя
        selected_item_id = message.text.strip()
        if not selected_item_id.isdigit():
            await message.answer("ID товара должен быть числом. Попробуйте еще раз.")
            return

        # Поиск товара в катологе
        items = product_catalog.get(selected_category, {}).get("items", [])
        if not items:
            await message.answer("Выбранная категория пуста или не существует.")
            return

        for item in items:
            if item["id"] == selected_item_id:
                user_cart = get_user_cart(user_id)
                user_cart.append(item)
                logger.info(f"Товар {item['name']} успешно добовлен в корзину "
                            f"пользователя {user_id}.")
                await message.answer(
                        f"Товар \"{item['name']}\" добавлен в корзину.",
                        reply_markup=create_item_detail_keyboard(selected_category)
                    )
                return

        logger.warning(f"Пользователь ({user_id}) попытался добавить товар с "
                       f"несуществуюшим ID: {selected_item_id}.")
        await message.answer("Товар с указаным ID не найден. Попробуйте еще раз.")
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {str(e)}.")
        await message.answer("Произошла системная ошибка. Попробуйте позже.")

# --- Просмотр корзины ---
@router.message(Command(commands=['cart']))
async def view_cart(message: Message):
    """Отображает содержимое корзины пользователя"""
    user_id = message.from_user.id

    if not isinstance(user_id, int): # Проверяем корректность user_id
        logger.warning("user_id некорректный или отсутствует в запросе на просмотр корзины.")
        await message.answer("Ошибка: не удалось обработать ваш запрос.")
        return

    logger.info(f"Пользователь ({user_id}) запросил просмотр корзины.")
    user_cart = get_user_cart(user_id)

    if not user_cart:
        logger.info(f"Корзина пользователя ({user_id}) пуста.")
        await message.answer("Ваша корзина пуста.")
    else:
        try:
            cart_items = "\n\n".join(
                [f"Название: {item["name"]}\nЦена: {item['price']} PLN"
                 for item in user_cart]
            )
            total_price = calculate_cart_total(user_cart)
            category_key = user_cart[0].get("category", "") if user_cart else ""

            logger.info(f"Пользователь ({user_id}) просмотрел корзину."
                        f" Итоговая сумма: {total_price} PLN. ")
            await message.answer(
                f"Ваши товары: \n\n{cart_items}\n\n Сумма к оплате:{total_price} PLN",
                reply_markup=create_item_detail_keyboard(category_key)
                )
        except Exception as e:
            logger.error(f"Ошибка при отображении корзины: {str(e)}.")
            await message.answer("Произошла ошибка при загрузке содержимого корзины.")


# --- Очистка корзины ---
@router.callback_query(lambda callback: callback.data == "cart_clear")
async def clear_cart(callback_query: CallbackQuery):
    """Очищает корзину пользователя"""
    user_id = callback_query.from_user.id

    if not isinstance(user_id, int): # Проверяем user_id
        logger.warning("user_id некорректный в запросе на очиску корзины.")
        await callback_query.message.edit_text("Ошибка: запрос не может быть обработан.")
        return

    CART_STORAGE[user_id] = []
    logger.info(f"Корзина пользователя ({user_id}) успешно очищена.")
    await callback_query.message.edit_text("Корзина успешно очищена.")

# --- Оформление заказа ---
@router.callback_query(lambda callback: callback.data == "cart_checkout")
async def checkout_cart(callback_query: CallbackQuery):
    """Завершает процесс оформления заказа"""
    user_id = callback_query.from_user.id

    if isinstance(user_id, int):
        logger.warning("user_id Некорректный в запросе на оформление заказа.")
        await callback_query.message.edit_text("Ошибка: запрос не может быть"
                                               "обработан.")
        return

    user_cart = get_user_cart(user_id)
    if not user_cart:
        logger.info(f"Пользователь ({user_id}) попытался оформить заказ с пустой корзиной.")
        await callback_query.message.edit_text("""Ваша корзина пуста. 
        Для оформления сделайте заказ""")
    else:
        try:
            total_price = calculate_cart_total(user_cart)
            CART_STORAGE[user_id] = []   # Очищение корзины после оформления
            logger.info(f"Пользователь ({user_id}) попытался оформить заказ на сумму"
                        f" {total_price} PLN.")
            await callback_query.message.edit_text(
                f"Спасибо за заказ!) Сумма к оплате: {total_price} PLN."
            )
        except Exception as e:
            logger.error(f"Ошибка при оформлении заказа: {str(e)}.")
            await callback_query.message.edit_text("Произошла ошибка при оформлении заказа."
                                                   "Попробуйте позже.")
