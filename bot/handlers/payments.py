import asyncio
import logging
import os
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = Router()

# TON wallet и BLIK конфигурация
TON_WALLET_ADDRESS = os.getenv("TON_WALLET_ADDRESS", "default_wallet_address")
BLIK_PHONE_NUMBER = os.getenv("BLIK_PHONE_NUMBER", "default_phone_number")

if TON_WALLET_ADDRESS == "default_wallet_address":
    logger.warning("TON_Wallet_ADDRESS использует значение по умолчанию!")
if BLIK_PHONE_NUMBER == "default_phone_number":
    logger.warning("BLIK_PHONE_NUMBER использует значение по умолчанию!")

# Константы для состояний
class PaymentStates:
    WARNING_BLIK_CONFIRMATION = "waiting_for_blik_confirmation"
    WARNING_TON_CONFIRMATION = "waiting_for_ton_confirmation"


def ton_payment_description(item_name: str, item_price: int) -> str:
    """Функция для генерации описания перевода на TON Wallet"""
    return (
        f"Оплата через TON Wallet\n\n"
        f"1. Переведите: {item_price / 100:.2f} TON на адрес: {TON_WALLET_ADDRESS}\n"
        f"2. Укажите в комментарии название товара: {item_name}\n"
        f"3. После оплаты подтвердите отправку, чтобы завершить заказ."
    )


def blik_payment_description(item_price: int):
    """Функция для генерации описания перевода через BLIK"""
    return (
        f"Оплата через BLIK.\n\n"
        f"1. Переведите {item_price / 100:.2f} "
        f"PLN на номер телефона: {BLIK_PHONE_NUMBER}\n"
        f"2. После перевода подтвердите заказ, чтобы завершить заказ."
    )


async def check_ton_transaction(wallet_address: str, item_price: int) -> bool:
    """Функция для проверки транзакции через TON WALLET"""
    try:
        logger.info(f"Идет проверка транзакции: адрес TON Wallet {wallet_address},"
                    f"сумма {item_price / 100:.2f} PLN")
        await asyncio.sleep(5)  # Здесь должна быть реальная проверка через API TON Wallet
        logger.info("Проверка транзакции прошла успешно.")
        return True  # Вернем True, если транзакция прошла успешно
    except Exception as e:
        logger.error("Ошибка при проверке транзакции: " + str(e))
        return False


@router.callback_query(lambda callback: callback.data.startswith("payment_"))
async def handle_payment_choice(callback: CallbackQuery, state: FSMContext):
    """Функция обработки выбора способа оплаты для пользователя"""
    try:
        payment_method = callback.data.split("_")[1]
        user_data = await state.get_data()
        # Проверка, выбран ли товар
        item = user_data.get("selected_item")
        if not item:
            await callback.message.answer(
                "Ошибка: Товар не выбран. Пожалуйста, начните заново.")
            return

        item_name = item.get("name")
        try:
            item_price = int(item.get("price", 0) * 100)  # Цена в копейках
        except (TypeError, ValueError) as e:
            logger.error(f"Ошибка вычисления цены товара: {str(e)}")
            await callback.message.answer("Ошибка: Некорректные данные о товаре.")
            return

        if not item_name or item_price <= 0:
            await callback.message.answer("Ошибка: Некорректные данные о товаре.")
            logger.warning("Не указаны имя или цена товара.")
            return

        if payment_method == "blik":
            await callback.message.answer(
                blik_payment_description(item_price), reply_markup=None
            )
            await state.set_state(PaymentStates.WARNING_BLIK_CONFIRMATION)
            logger.info("Пользователь выбрал оплату через BLIK.")

        elif payment_method == "ton":
            await callback.message.answer(
                ton_payment_description(item_name, item_price),
                reply_markup=None
            )
            await state.set_state(PaymentStates.WARNING_TON_CONFIRMATION)
            logger.info("Пользователь выбрал оплату через TON Wallet.")
        else:
            await callback.message.answer("Неподдерживаемый способ оплаты.")
            logger.error(f"Ошибка обработки платежного выбора: {payment_method}")
    except Exception as e:
        logger.error(f"Ошибка обработки платежного выбора: {str(e)}")
        await callback.messenger.answer("Произошла ошибка. Попробуйте еще раз.")

# Обработчик подтверждения платы через BLIK
@router.message(StateFilter(PaymentStates.WARNING_BLIK_CONFIRMATION))
async def confirm_blik_payment(message: Message, state: FSMContext):
    """Функция подтверждения платы через BLIK"""
    try:
        await state.clear()
        if not await state.get_state():
            logger.info("Состояние успешно очищено.")
        await message.answer("Спасибо за оплату через BLIK!" 
                             "Ваш заказ принят и обрабатывается.")
        logger.info("Оплата через BLIK подтверждена.")
    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты BLIK: {str(e)}")
        await message.answer("Произошла ошибка во время подтверждения."
                             " Попробуйте еще раз.")


# Обработчик подтверждения оплаты через TON Wallet
@router.message(StateFilter(PaymentStates.WARNING_TON_CONFIRMATION))
async def confirm_ton_payment(message: Message, state: FSMContext):
    """Функция подтверждения платы через TON Wallet"""
    try:
        await message.answer("Подтверждение оплаты TON. Пожалуйста, подождите...")
        item_price = int((await state.get_data()).get("selected_item",
                                                      {}).get("price", 0) * 100)

        # Проверка транзакции
        is_valid_ton = await check_ton_transaction(TON_WALLET_ADDRESS, item_price)
        if is_valid_ton:
            await state.clear()
            if not await state.get_state():
                logger.info("Состояние успешно очищено.")
            await message.answer("Спасибо за оплату через TON!"
                                 "Ваш заказ принят и обрабатывается")
            logger.info("Транзакция TON Wallet подтверждена.")
        else:
            await message.answer("Ошибка оплаты через TON Wallet."
                                 "Пожалуйста, попробуйте еще раз.")
            logger.warning("Транзакция TON Wallet недействительна.")
    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты TON: {str(e)}")
        await message.answer("Произошла ошибка во время подтверждения."
                             "Попробуйте еще раз.")
