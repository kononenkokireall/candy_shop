# Точка входа в приложение
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
# Импорт маршрутизаторов и обработчиков
from handlers.help import router as help_router
from handlers.catalog import router as catalog_router
from handlers.cart import router as cart_router
from handlers.payments import router as payments_router
from handlers.start import router as start_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Инициация маршрутизатора и хранилища состояний

#router = Router()
storage = MemoryStorage()  # Хранилище состояний памяти


async def main():
    """
    Главная функция, которая запускает бота.
    Все настройки и запуск логики бота происходят в этой функции.
    Функция выполняет следующие действия:
    Создает объект бота Bot с токеном BOT_TOKEN.
    Создает диспетчер Dispatcher для обработки событий.
    Подключает маршрутизатор router, где зарегистрированы обработчики 
    команд.
    Удаляет все старые веб-хуки с
    помощью bot.delete_webhook(drop_pending_updates=True). 
    Это важно для предотвращения накопления старых обновлений.
    Запускает режим polling, чтобы бот мог получать обновления и 
    обрабатывать их.
    """
    # Считывание файла токена
    try:
        with open("TOKEN_FILE.txt", 'r', encoding="UTF-8") as file_token:
            api_token = file_token.read().strip()
    except FileNotFoundError:
        logger.error("Файл с токеном не найден!")
        return
    # Инициация бота и диспетчера
    local_bot = Bot(
        token=api_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    local_dp = Dispatcher(storage=storage)
    local_dp.include_router(start_router)
    local_dp.include_router(catalog_router)
    local_dp.include_router(cart_router)
    local_dp.include_router(payments_router)
    local_dp.include_router(help_router)
    

    print("Бот запущен...")
    await local_bot.delete_webhook(drop_pending_updates=True)
    await local_dp.start_polling(local_bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Бот упал с ошибкой: {e}")
