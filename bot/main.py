# Точка входа в приложение
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from states import OrderProcess

# Инициация маршрутизатора и хранилища состояний

router = Router()
storege = MemoryStorage()  # Хранилище состояний памяти

# Обрабочик команды /Start


@router.message(Command('start'))
# Декоратор @router.message() для обработки сообщений с командой start.
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Функция:
    Принимает объект сообщения message.
    Отправляет ответное сообщение "Привет! Я твой бот. Чем могу помочь?" 
    пользователю, вызвавшему команду.
    Применение:
    Начинает процесс регистрации, устанавливая начальное состояние.
    """
    await state.set_state(OrderProcess.Registration)
    await message.answer("Привет! Пожалуйста, зарегистрируйтесь. Как вас зовут?")


@router.message(OrderProcess.Registration)
async def handle_registration(message: Message, state: FSMContext):
    """
    Обрабатывает ввод даных пользователя при резистрации
    """
    user_name = message.text
    # Сохраняем имя в контексте состояния
    await state.update_data(name=user_name)
    await state.set_state(OrderProcess.Greeting)
    await message.answer(f"Рад с Вами познакомится {user_name} ! Чем могу помочь?")
# Обработчик команды /Help


@router.message(Command('help'))
async def cmd_help(message: Message):
    """
    Описание:
    Отправляет пользователю список доступных команд и их краткое описание.
    Применение:
    Показывает справку пользователю, чтобы он мог разобраться, какие 
    команды доступны в боте.
    """
    await message.answer('''Инфо.помощь. Доступные Команды:
                            /Start - Начать работу с ботом
                            /Help  - Получить инфо. о функиях бота''')


@router.message(OrderProcess.Greeting)
async def handle_greeting(message: Message, state: FSMContext):
    """
    Обрабатывает действия после приветствия
    """
    await state.set_state(OrderProcess.SelectItem)
    await message.answer("""Пожайлуста сделайте выбор товара. Напишите номер 
                            товара(Пример: 4231)
                        """)


@router.message(OrderProcess.SelectItem)
async def handle_select_item(message: Message, state: FSMContext):
    """
    Обрабатывает выбор товара
    """
    selected_item = message.text
    await state.update_data(item=selected_item)
    await state.set_state(OrderProcess.Payment)
    await message.answer(f"Вы выбрали товар {selected_item}. Выберите способ оплаты: ")
# Обработчик текста


@router.message(OrderProcess.Payment)
async def handle_payment(message: Message, state: FSMContext):
    """
    Обрабатывает способ оплаты пользывателя
    """
    payment_method = message.text
    user_data = await state.get_data()  # Получение сохраненых данных
    item = user_data.get('item')
    await state.set_state(OrderProcess.Confirmation)
    await message.answer(f"""Вы выбрали метод оплаты: {payment_method}.
                         Подтвердите заказ на {item} да/нет """)


@router.message(OrderProcess.Confirmation)
async def handle_confirmation(message: Message, state: FSMContext):
    """
    Обрабатывает подтверждение заказа
    """
    if message.text.lower() in ['да', 'нет']:
        await message.answer("Ваш заказ принят! Спасибо за покупку.")
        await state.clear()  # Сбрасиваем состояние
    else:
        await message.answer("""Заказ отменен. 
                             Нажмите /start что бы занова начать роботу с ботом""")
        await state.clear()

# Основная функция для запуска бота

async def main():
    """
    Главная функция, которая запускает бота.
    Функция выполняет следующие действия:
    Создает объект бота Bot с токеном BOT_TOKEN.
    Создает диспетчер Dispatcher для обработки событий.
    Подключает маршрутизатор router, где зарегистрированы обработчики 
    команд (start_command, help_command и другие).
    Удаляет все старые вебхуки с 
    помощью bot.delete_webhook(drop_pending_updates=True). Это важно для 
    предотвращения накопления старых обновлений.
    Запускает режим polling, чтобы бот мог получать обновления и 
    обрабатывать их.
    Применение:
    Это точка входа для запуска бота.
    Все настройки и запуск логики бота происходят в этой функции.
    """
    # Считывание файла токена
    with open("TOKEN_FILE.txt", 'r', encoding="UTF-8") as file_token:
        api_token = file_token.read().strip()
    # Инициация бота и диспетчера
    local_bot = Bot(
        token=api_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    local_dp = Dispatcher()
    local_dp.include_router(router)

    print("Бот запущен...")
    await local_bot.delete_webhook(drop_pending_updates=True)
    await local_dp.start_polling(local_bot)

if __name__ == "__main__":
    asyncio.run(main())
