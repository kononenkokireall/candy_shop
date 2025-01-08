"""Этот модуль содержит обработчики для работы с каталогом товаров."""
import logging
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from ..data.catalog_data import PRODUCT_CATALOG
from ..states import OrderProcess
from ..keyboards import (create_catalog_keyboard, create_payment_methods_keyboard,
                         create_item_detail_keyboard)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для префиксов callback_данных
CATALOG_PREFIX = "catalog_"
CATEGORY_PREFIX = "category_"
ADD_TO_CART_PREFIX = "add_to_cart_"

router = Router()

# Обработчик нажатия на кнопку каталога
@ router.callback_query(lambda callback: callback.data.startswith(CATALOG_PREFIX))
async def user_catalog(callback: CallbackQuery):
    """Обработка выбора категории из каталога и вывод списка товаров."""
    category_key = callback.data.replace("catalog_", "")
    logger.info(f"Пользователь {callback.from_user.id} выбрал категорию {category_key}")

    # Проверяем наличие категории в каталоге
    if category_key in PRODUCT_CATALOG:
        item = PRODUCT_CATALOG[category_key]

        # Проверка наличия необходимых данных в товаре
        if not all(key in item for key in ("name", "description", "price")):
            await callback.message.answer("Данные выбранного продукта некорректны.")
            logger.error(f"Некорректные данные в продукте: {item}")
            return

        try:
            await callback.message.edit_text(
                f"<b>{item['name']}</b>\n\n"
                f"{item['description']}\n"
                f"Цена: {item['price']}",
                reply_markup=create_item_detail_keyboard(category_key)
            )
            logger.info(f"Категория {category_key} успешно обработана для пользователя"
                        f" {callback.from_user.id}.")
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения: {str(e)}")
            await callback.message.answer("Произошла ошибка при обработке запроса.")
    else:
        await callback.message.answer("Извините, выбранная категория временно отсутствует.")
        logger.warning(f"Категория {category_key} не найдена пользователем "
                       f"{callback.from_user.id}.")


@router.callback_query(lambda callback_query: callback_query.data.startswith(CATEGORY_PREFIX))
async def handle_category_selection(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор категории и отображает список товаров внутри нее.
    """
    category_key = callback_query.data.split("_")[1]
    logger.info(f"Выбор категории: {category_key}, Пользователь:"
    f"{callback_query.from_user.id}")

    category = PRODUCT_CATALOG.get(category_key)

    # Проверка существования категории и ее данных
    if not category or not isinstance(category, dict) or "items" not in category.keys()\
            or not isinstance(category["items"], list):
        await callback_query.message.answer("Категория пуста или данные некорректны.")
        logger.error(f"Категория {category_key} пуста или имеет некорректные данные для"
                     f"пользователя {callback_query.from_user.id}.")
        return

    try:
        await state.update_data(selected_category=category_key)
        items = "\n\n".join([
            f"ID: {item['id']}\nНазвание: {item['name']}\nОписание: {
            item['description']}\nЦена: {item['price']} PLN."
            for item in category["items"]
        ])
        await callback_query.message.answer(
            f"Категория: {category['name']}\n\n{items}\n\n"
            f"Для добавления товара в корзину напишите его ID."
        )
        logger.info(f"Подкатегория {category_key} обработка для пользователя"
                    f"{callback_query.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке категории {category_key}: {str(e)}")
        await callback_query.message.answer("Произошла ошибка при обработке категории.")


# Обработчик нажатия на кнопку (Добавить товар в корзину)
@ router.callback_query(lambda callback: callback.data.startswith(ADD_TO_CART_PREFIX))
async def handle_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавление выбранного товара в корзину пользователя."""
    category_key = callback.data.replace(ADD_TO_CART_PREFIX, "")
    logger.info(f"Пользователь: {callback.from_user.id} добавляет товар в"
                f"корзину {category_key}")

    item = PRODUCT_CATALOG.get(category_key)
    if item:
        try:
            # Сохраняем товар в корзину в контексте состояния пользователя.
            user_data = await state.get_data()
            cart = user_data.get("cart", [])
            cart.append(item)
            await state.update_data(cart=cart)

            await callback.message.answer(
                f"Товар {item['name']}, добавлен в корзину.\n"
                f"Желаете продолжить покупки?",
                reply_markup=create_catalog_keyboard(PRODUCT_CATALOG)
            )
            logger.info(f"Товар {item['name']} успешно добавлен в корзину пользователем "
                        f"{callback.from_user.id}.\n")
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара {category_key} в корзину: {str(e)}")
            await callback.message.answer("Ошибка добавления товара в корзину.")
    else:
        await callback.message.answer("Ошибка добавления товара в корзину.")
        logger.warning(f"Товар {category_key} не найден для пользователя"
                       f" {callback.from_user.id}.")


# Обработчик команды для просмотра корзины
@ router.message(lambda message: message.text.lower() == "ваша корзина")
async def user_view_cart(message: Message, state: FSMContext):
    """
    Извлекает данные корзины из состояния пользователя.
    """
    logger.info(f"Просмотр корзины, Пользователь: {message.from_user.id}")
    try:
        user_data = await state.get_data()
        if not user_data:
            await message.answer("Не удалось получить данные вашего состояния.")
            return

        cart = user_data.get('cart', [])
        if cart:
            cart_text = "Ваши товары в корзине: \n\n" + "\n".join(
                [f"{item['name']} - {item['price']} PLN" for item in cart]
            )
            await message.answer(cart_text)
            logger.info(f"Корзина пользователя {message.from_user.id}: {cart}")
        else:
            await message.answer("Ваша корзина пуста.")
            logger.info(f"Корзина пользователя {message.from_user.id} пуста.")
    except Exception as e:
        logger.error(f"Ошибка при просмотре корзины пользователя"
                     f"{message.from_user.id}: {str(e)}")
        await message.answer("Произошла ошибка при просмотре корзины.")


# Обработчик нажатия кнопки(Выбрать способ оплаты)
@ router.callback_query(lambda callback: callback.data == "choose_payment")
async def user_choose_payment(callback: CallbackQuery, state: FSMContext):
    """Устанавливает состояние пользователя как OrderProcess"""
    logger.info(f"Пользователь: {callback.from_user.id} выбирает способ оплаты.")
    try:
        await state.set_state(OrderProcess.Payment)
        await callback.message.edit_text(
            "Выберите способ оплаты: ", reply_markup=create_payment_methods_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} успешно перешел на этап выбора"
                    f"способа оплаты.")
    except Exception as e:
        logger.error(f"Ошибка при выборе способа оплаты {callback.from_user.id}: {str(e)}")
        await callback.message.answer("Произошла ошибка при выборе способа оплаты.")