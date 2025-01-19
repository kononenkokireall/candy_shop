# Точка входа в приложение
import os
import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv, find_dotenv


# Импорт маршрутизаторов и обработчиков
from handlers.start import router as user_start
from handlers.group_user import user_group_router
from handlers.admin import admin_router

from common.bot_cmds_list import private

load_dotenv(find_dotenv())

ALLOWED_UPDATES = ['message', 'edited_message']


# Настройка логирования
try:
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL, logging.INFO),
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
except AttributeError:
    logging.warning("Некорректное значение LOGGING_LEVEL. Установлено значение INFO.")
    logging.basicConfig(level=logging.INFO,)

logger = logging.getLogger(__name__)


async def main():
    """
    Главная асинхронная функция для запуска бота:
    - Загружает токен из файла или переменной окружения.
    - Инициализирует бота и диспетчер событий.
    - Регистрирует маршруты (handlers).
    - Запускает polling для обработки обновлений.
    """
    bot = Bot(token=os.getenv("TOKEN"),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.my_admins_list = []
    local_dp = Dispatcher()

    # Регистрация маршрутов
    logger.info("Регистрация маршрутов...")
    local_dp.include_router(user_start)
    local_dp.include_router(user_group_router)
    local_dp.include_router(admin_router)
    logger.info("Маршруты успешно зарегистрированы.")


    try:
        logger.info("Удаление веб-хуков с параметром drop_pending_updates=True...")
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.exception(f"Ошибка удаления веб-хуков: {str(e)}")
        return


    # Обработка сигналов для корректного завершения
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_signals():
        logger.info("Получен сигнал завершения. Завершенем бота...")
        stop_event.set()
        loop.stop()

    for signame in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signame, shutdown_signals)

    # Запуск polling
    try:
        logger.info("Бот зарущен. Ожидание событий...")
        await local_dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)
    finally:
        logger.info("Закрытие сесии бота...")
        await bot.session.close()
        logger.info("Сессия закрыта. Бот завершен.")


if __name__ == "__main__":
    try:
        logger.info("Инициализация asyncio event loop...")
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Бот упал с ошибкой: {str(e)}")
