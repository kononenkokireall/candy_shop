# Точка входа в приложение
import os
import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv, find_dotenv

from middlewares.db import DataBaseSession

load_dotenv(find_dotenv())

from database.engine import create_db, drop_db, session_marker


# Импорт маршрутизаторов и обработчиков
from handlers.start import router as user_start
from handlers.group_user import user_group_router
from handlers.admin import admin_router


ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query']

# Настройка логирования
try:
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL, logging.INFO),
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
except AttributeError:
    logging.warning("Некорректное значение LOGGING_LEVEL. Установлено значение INFO.")
    logging.basicConfig(level=logging.INFO,)

logger = logging.getLogger(__name__)

# Загружает токен из файла или переменной окружения.
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

async def on_startup(bot):
    run_param = False
    if run_param:
        await drop_db()
    await create_db()

async def on_shutdown(bot):
    print('bot shutdown')


async def main():
    """
    Главная асинхронная функция для запуска бота:
    - Инициализирует базу данных.
    - Запускает polling для обработки обновлений.
    """
    local_dp.startup.register(on_startup)
    local_dp.shutdown.register(on_shutdown)
    local_dp.update.middleware(DataBaseSession(session_pool=session_marker))
    try:
        logger.info("Удаление веб-хуков...")
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.exception(f"Ошибка удаления веб-хуков: {str(e)}")
        return


    # Обработка сигналов для корректного завершения
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown_signals():
        logger.info("Получен сигнал завершения. Завершенем работу бота...")
        stop_event.set()
        loop.stop()

    for signame in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signame, shutdown_signals)

    # Запуск polling
    try:
        logger.info("Бот зарущен. Ожидание событий...")
        await local_dp.start_polling(bot, allowed_updates=local_dp.resolve_used_update_types())
    finally:
        logger.info("Закрытие сессии бота...")
        await bot.session.close()
        logger.info("Сессия закрыта. Бот завершил работу.")


if __name__ == "__main__":
    try:
        logger.info("Инициализация asyncio event loop...")
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Бот упал с ошибкой: {str(e)}")
