# Точка входа в приложение
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import Router
from aiogram.fsm.storage.memory import MemoryStorage
from states import OrderProcess

# Инициация маршрутизатора и хранилища состояний

router = Router()
storege = MemoryStorage()  # Хранилище состояний памяти


async def main():
    """
    Главная функция, которая запускает бота.
    Все настройки и запуск логики бота происходят в этой функции.
    Функция выполняет следующие действия:
    Создает объект бота Bot с токеном BOT_TOKEN.
    Создает диспетчер Dispatcher для обработки событий.
    Подключает маршрутизатор router, где зарегистрированы обработчики 
    команд.
    Удаляет все старые вебхуки с 
    помощью bot.delete_webhook(drop_pending_updates=True). 
    Это важно для предотвращения накопления старых обновлений.
    Запускает режим polling, чтобы бот мог получать обновления и 
    обрабатывать их.
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
