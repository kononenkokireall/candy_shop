from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto # TODO


router = Router()

# Путь к фотоинструкциям
HELP_IMAGES = {
    "start": "example_image(images/help_start.jpg)",
    "catalog": "example_image(images/help_start.jpg)",
    "order": "example_image(images/help_start.jpg)",
    "payment": "example_image(images/help_start.jpg)",
    "blik": "example_image(images/help_start.jpg)",
    "ton": "example_image(images/help_start.jpg)",
}

# Текст инструкции
HELP_TEXT = {
    "start": """Добро пожаловать! Вот как начать работу с ботом:\n
                1.Используйте команду start для начала.\n
                2. Выберите интересующую вас категорию из каталога.""",
    "catalog": """Как выбрать товар:\n
                1. Войдите в каталог.\n
                2. Выберите товар для
                подробного описания.\n
                3. Нажмите кнопку 'Добавить в корзину', 
                если хотите заказать этот товар.""",
    "order": """Как оформить заказ:\n
                1. Перейдите в корзину командой 
                'Ваша корзина'.\n
                2. Проверьте выбранные товары.\n
                3. Нажмите 'Оформить заказ' для продолжения.""",
    "payment": """Как оплатить заказ:\n
                1. Выберите способ оплаты после оформления 
                заказа.\n
                2. Следуйте инструкциям для выбранного метода оплаты.""",
    "blik": """Оплата через BLIK:\n
                1. Выберите BLIK как способ оплаты.\n
                2. Введите 6-значный код BLIK.\n
                3. Дождитесь подтверждения успешной оплаты.""",
    "ton": """Оплата через TON Wallet:\n1. 
                Выберите TON Wallet как способ оплаты.\n2. 
                Переведите указанную сумму на адрес кошелька.\n
                3. Укажите название товара в комментарии к платежу.""",
}


@router.message(lambda message: message.text.lower() == "помощь")
async def user_help(message: Message, state: FSMContext): #TODO
    """
    Функция вызова поддержки бота
    """
    await message.text("Добро пожаловать в раздел помощи! Вот основные темы:")

    for section, text in HELP_TEXT.items():
        if section in HELP_IMAGES:
            photo_path = HELP_IMAGES[section]
            await message.answer_photo(
                photo=open(photo_path, 'rb'), caption=text
            )
        else:
            await message.answer(text)

    await message.answer("""Если у вас остались вопросы,
                         напишите в  тех.поддержку(ссылка на чат)""")
