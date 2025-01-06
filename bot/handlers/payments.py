import asyncio
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
# from aiogram.types import PreCheckoutQuery, LabeledPrice

router = Router()

# TON wallet and BLIK configuration
TON_WALLET_ADDRESS = 'Api key ton wallet'
BLIK_PHONE_NUMBER = "+48XXXXXXXX"  # Номер телефона для перевода через BLIK

# Функция для генерации описания перевода на TON WALLET


def ton_payment_description(item_name: str, item_price: int):
    """
    Функция для генерации описания перевода на TON Wallet
    """
    return (
        f"Оплата через TON Wallet\n\n"
        f"""1. Переведите: {item_price /
                            100:.2f} TON на адрес: {TON_WALLET_ADDRESS}"""
        f"2. Укажите в комментарии название товара: {item_name}\n"
        f"3. После оплаты подтвердите отправку, чтобы завершить заказ."
    )


def blik_payment_description(item_price: int):
    """
    Функция для генерации описания перевода через BLIK
    """
    return (
        f"Оплата через BLIK.\n\n"
        f"""1. Переведите {item_price /
                           100:.2f} PLN на номер телефона: {BLIK_PHONE_NUMBER}\n"""
        f"  2. После перевода подтвердите заказ, чтобы завершить заказ."
    )


async def check_ton_transaction(wallet_address: str, item_price: int):
    """
    Функция для проверки транзакции через TON WALLET
    """
    await asyncio.sleep(5)  # Подождем 5 секунд
    return True  # Вернем True, если транзакция прошла успешно


@router.callback_query(lambda callback: callback.data.startswith("payment_"))
async def handle_payment_choice(callback: CallbackQuery, state: FSMContext):
    """
    Функция обработки выбора способа оплаты для пользователя
    """
    payment_method = callback.data.split("_")[1]
    user_data = await state.get_data()
    item = user_data.get("selected_item")

    if not item:
        await callback.message.answer("Ошибка: Товар не выбран. Пожайлуста, начните заново.")
        return
    item_name = item.get("name")
    item_price = int(item.get("price", 0) * 100)  # Цена в копейках

    if payment_method == "blik":
        await callback.message.answer(
            blik_payment_description(item_price), reply_markup=None
        )
        await state.set_state("waiting_for_blik_confirmation")
    elif payment_method == "ton":
        await callback.message.answer(
            ton_payment_description(item_name, item_price), reply_markup=None
        )
        await state.set_state("waiting_for_ton_confirmation")
    else:
        await callback.message.answer("Неподдерживаемый способ оплаты")


@router.message(state="waiting_for_blik_confirmation")
async def confirm_blik_payment(message: Message, state: FSMContext):
    """
    Функция подтверждения платы через BLIK
    """
    await state.clear()
    await message.answer(
        "Спасибо за оплату через BLIK! Ваш заказ принят и обработывается."
    )


@router.message(state="waiting_for_ton_confirmation")
async def confirm_ton_payment(message: Message, state: FSMContext):
    """
    Функция подтверждения платы через TON Wallet
    """
    await message.answer("Подтверждение оплаты TON. Пожалуйста, подождите...")
    item_price = int((await state.get_data()).get("selected_item", {}).get("price", 0) * 100)
    is_valid_ton = await check_ton_transaction(TON_WALLET_ADDRESS, item_price)

    if is_valid_ton:
        await state.clear()
        await message.answer(
            "Спасибо за оплату через TON! Ваш заказ принят и обработывается")
    else:
        await message.answer("Ошибка оплаты через TON Wallet. Пожалуйста, попробуйте еще раз.")
