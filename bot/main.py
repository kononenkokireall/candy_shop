# Точка входа в приложение
import os
import asyncio
import logging
from pathlib import Path
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
try:
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL.upper(), logging.INFO),
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
except AttributeError:
    logging.warning("Некорректное значение LOGGING_LEVEL. Установлено значение INFO.")
    logging.basicConfig(level=logging.INFO,)

logger = logging.getLogger(__name__)

# Хранилище состояний памяти для FSM
storage = MemoryStorage()


async def main():
    """
    Главная асинхронная функция запуска бота
    - Чтение токена из файла.
    - Инициализация бота и диспетчера.
    - Регистрация маршрутов.
    - Запуск polling для обработки обновлений.
    """
    logger.info("Запуск бота...")

    # Считывание файла токена
    try:
        TOKEN_FILE_PATH = Path(os.getenv("TOKEN_FILE_PATH", "TOKEN_FILE.txt"))
        logger.debug(f"Попытка открыть файл токена: {TOKEN_FILE_PATH}...")

        if not TOKEN_FILE_PATH.exists():
            logger.error(f"Файл с токен {TOKEN_FILE_PATH} не найден!")
            return

        with TOKEN_FILE_PATH.open( 'r', encoding="UTF-8") as file_token:
            api_token = file_token.read().strip()

        if not api_token or len(api_token) < 10:
            logger.error("Токен пуст. Проверьте содержание файла TOKEN_FILE.txt.")
            return
        logger.info("Токен успешно считан.")
    except Exception as e:
        logger.error(f"Ошибка чтения файла токена: {str(e)}")
        return

    # Инициация бота и диспетчера
    local_bot = Bot(
        token=api_token,
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

    # Запуск бота
    try:
        logger.info("Удаление веб-хуков с параметром drop_pending_updates=True...")
        await local_bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Ошибка удаления веб-хуков: {str(e)}")
        return

    # Основной цыкла запуска polling
    while True:
        try:
            logger.info("Запуск polling...")
            await local_dp.start_polling(local_bot)
        except Exception as e:
            logger.info(f"Ошибка ва время запуска polling: {str(e)}"
                        f"Перезапуск через 5 секунд...")
            await asyncio.sleep(5)
        finally:
            logger.info("Завершение работы с ботом. Закрытие сессии...")

        # Закрытие сессии
        if 'local_bot' in locals():
            await local_bot.session.close()


if __name__ == "__main__":
    try:
        logger.info("Инициализация asyncio event loop...")
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Бот упал с ошибкой: {str(e)}")
