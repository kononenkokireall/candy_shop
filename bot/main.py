# Точка входа в приложение
from aiogram import Bot, Dispatcher # TODO
from aiogram.types import Message
from aiogram.filters import Command
import asyncio

# Считывание файла токена
with open('TOKEN_FILE.txt', 'r', encoding='UTF-8') as token:
    TOKEN = token.read()
# Токен бота
API_TOKEN = TOKEN

# Инициация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Обрабочик команды /Start


@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer("Инфо про магазин")

# Обработчик команды /Help


@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Инфо про помощь')

# Обработчик текста


@dp.message()
async def echo_handler(message: Message):
    await message.answer(f'Вы написали {message.text}')

# Основная функция для запуска бота


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
