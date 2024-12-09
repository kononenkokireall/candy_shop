# Точка входа в приложение
import asyncio
from aiogram import Bot, Dispatcher  # TODO
from aiogram.types import Message
from aiogram.filters import Command

# Считывание файла токена
with open('TOKEN_FILE.txt', 'r', encoding='UTF-8') as token:
    TOKEN = token.read()
# Токен бота
API_TOKEN = TOKEN

# Инициация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
dp.include_router(bot)

# Обрабочик команды /Start


@dp.message(Command('start'))
async def cmd_start(message: Message):
    """
    Это обработчик команды /start.
    Использует декоратор @router.message() для обработки сообщений с командой start.
    Функция:
    Принимает объект сообщения message.
    Отправляет ответное сообщение "Привет! Я твой бот. Чем могу помочь?" пользователю, вызвавшему команду.
    Применение:
    Приветствие пользователя при первом запуске бота.
    Может быть дополнена логикой для предоставления инструкций или начальной информации.
    """
    await message.answer("Инфо про магазин")

# Обработчик команды /Help


@dp.message(Command('help'))
async def cmd_help(message: Message):
    """
    Описание:
    Обрабатывает команду /help.
    Отправляет пользователю список доступных команд и их краткое описание.
    Принимает объект сообщения message.
    Применение:
    Показывает справку пользователю, чтобы он мог разобраться, какие команды доступны в боте.
    """
    await message.answer('Инфо про помощь')

# Обработчик текста


@dp.message()
async def echo_handler(message: Message):
    """
    Описание:
    Это базовый обработчик всех текстовых сообщений, которые не соответствуют другим командам.
    Берет текст из сообщения пользователя и отправляет его обратно с пометкой: "Вы написали: ...".
    Применение:
    Используется для тестирования или обработки непредвиденных сообщений.
    Может быть улучшен для обработки сложных пользовательских запросов.
    """
    await message.answer(f'Вы написали {message.text}')

# Основная функция для запуска бота


async def main():
    """
    Главная функция, которая запускает бота.
    Функция выполняет следующие действия:
    Создает объект бота Bot с токеном BOT_TOKEN.
    Создает диспетчер Dispatcher для обработки событий.
    Подключает маршрутизатор router, где зарегистрированы обработчики команд (start_command, help_command и другие).
    Удаляет все старые вебхуки с помощью bot.delete_webhook(drop_pending_updates=True). Это важно для предотвращения накопления старых обновлений.
    Запускает режим polling, чтобы бот мог получать обновления и обрабатывать их.
    Применение:
    Это точка входа для запуска бота.
    Все настройки и запуск логики бота происходят в этой функции.
    """
    print("Бот запущен...")
    await dp.start_polling(bot)
    bot = Bot(token=API_TOKEN, parse_mode="HTML")
if __name__ == "__main__":
    asyncio.run(main())
