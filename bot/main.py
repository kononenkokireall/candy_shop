# Точка входа в приложение
import os
import asyncio
import logging
import signal
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, TelegramObject
from aiogram import Router
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Awaitable, Any

# Импорт маршрутизаторов и обработчиков
from handlers.help import router as help_router
from handlers.catalog import router as catalog_router
from handlers.cart import router as cart_router
from handlers.payments import router as payments_router
from handlers.start import router as start_router

# Настройка логирования
try:
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL, logging.INFO),
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
except AttributeError:
    logging.warning("Некорректное значение LOGGING_LEVEL. Установлено значение INFO.")
    logging.basicConfig(level=logging.INFO,)

logger = logging.getLogger(__name__)

# Хранилище состояний памяти для FSM
storage = MemoryStorage()

# Middleware для логирования
class UpdateLoggerMiddkeware(BaseMiddleware):
    """ Middleware для логирования всех обновлений"""
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:  # pragma: no cover
        logger.warning(f"Необработанное обновление: {event.dict()}")
        return await handler(event, data)


async def load_api_token() -> str:
    """
    Считывает токен из файла или из переменной окружения.
    """
    # Считывание файла токена
    token_file_path = Path(os.getenv("TOKEN_FILE_PATH", "TOKEN_FILE.txt"))
    logger.debug(f"Попытка открыть файл токена: {token_file_path}...")
    try:
        if token_file_path.exists():
            logger.info(f"Попытка загрузить токен из файла {token_file_path}...")
            with token_file_path.open( 'r', encoding="UTF-8") as file_token:
                token = file_token.read().strip()
                if token and len(token) >= 10: # Простая проверка длины токена
                    return token
            raise ValueError("Файл токена найден, но он пустой или токен "
                                 "слишком короткий.")
        else:
            logger.warning(
                f"Файл токена {token_file_path} не найден, попытка загрузить"
                f"токен из переменной окружения.")
    except Exception as e:
        logger.error(f"Ошибка при чтении токена из файла: {str(e)}")

    # Загрузка токена из переменной окружения
    token_env_name = os.getenv("TOKEN_ENV_NAME", "")
    if token_env_name and len(token_env_name) >= 10:
        logger.info("Токен успешно загружен из переменной окружения.")
        return token_env_name

    raise RuntimeError(
        "Не удалось найти токен бота. Убедитесь что файл токена или "
        "переменная окружения BOT_API_TOKEN указывают верное значение."
    )

    # Инициация бота и диспетчера
async def main():
    """
    Главная асинхронная функция для запуска бота:
    - Загружает токен из файла или переменной окружения.
    - Инициализирует бота и диспетчер событий.
    - Регистрирует маршруты (handlers).
    - Запускает polling для обработки обновлений.
    """
    # Загрузка токена
    API_TOKEN = await load_api_token()

    # Инициализация бота диспетчера
    local_bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"))
    local_dp = Dispatcher(storage=storage)

    # Регистрация маршрутов
    logger.info("Регистрация маршрутов...")
    local_dp.include_router(start_router)
    local_dp.include_router(catalog_router)
    local_dp.include_router(cart_router)
    local_dp.include_router(payments_router)
    local_dp.include_router(help_router)
    logger.info("Маршруты успешно зарегистрированы.")

    # Регистрация роутера для необработанных событий
    local_dp.message.middleware(UpdateLoggerMiddkeware())

    try:
        logger.info("Удаление веб-хуков с параметром"
                        " drop_pending_updates=True...")
        await local_bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Ошибка удаления веб-хуков: {str(e)}")
        return


    # Обработка сигналов для корректного завершения
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_signals():
        logger.info("Получен сигнал завершения. Завершенем бота...")
        stop_event.set()
        loop.stop()
        return True

    for signame in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signame, shutdown_signals)

    # Запуск polling
    try:
        logger.info("Бот зарущен. Ожидание событий...")
        await local_dp.start_polling(local_bot, stop_event=stop_event)
    finally:
        logger.info("Закрытие сесии бота...")
        await local_bot.session.close()
        logger.info("Сессия закрыта. Бот завершен.")


if __name__ == "__main__":
    try:
        logger.info("Инициализация asyncio event loop...")
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Бот упал с ошибкой: {str(e)}")
