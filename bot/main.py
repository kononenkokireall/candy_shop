"""
Основной модуль Telegram-бота.
Организация работы бота, роутинга и взаимодействия с базой данных.
"""
import asyncio
import logging
from typing import Final

# Импорт компонентов aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
# Настройки бота по умолчанию
from aiogram.enums import ParseMode
# Режимы форматирования сообщений
from aiogram.types import BotCommand
# Модель для команд бота

# Импорт компонентов проекта
from database.engine import session_maker, create_db
# Работа с SQLAlchemy
from handlers.admin_events.admin_main import admin_router
# Роутер для админ-панели
from handlers.user_events.user_group import (
    user_group_router,
)  # Роутер для групповых чатов
from handlers.user_events.user_main import (
    user_private_router,
)  # Роутер для личных чатов
from middlewares.db import DataBaseSession
# Middleware для работы с БД
from utilit.config import settings

# Настройки из .env файла

# Настройка системы логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования INFO и выше
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # Формат сообщений
    force=True,  # Перезапись существующих обработчиков логирования
)
# Снижаем уровень логирования для aiogram, чтобы избежать спама
logging.getLogger("aiogram").setLevel(logging.WARNING)

# Список команд бота для отображения в интерфейсе Telegram
BOT_COMMANDS: Final = [
    BotCommand(command="start", description="Старт"),
    BotCommand(command="help", description="Помощь")
]
# Инициализация бота с токеном из настроек и HTML-форматированием
bot = Bot(
    token=settings.BOT_TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML)
)

bot.my_admins_list = []
# Создание диспетчера для обработки входящих сообщений
dp = Dispatcher()


def register_routers() -> None:
    """
    Регистрация всех роутеров в диспетчере.
    Роутеры отвечают за обработку разных типов сообщений:
    - Личные сообщения
    - Групповые чаты
    - Админ. Команды
    """
    routers = (user_private_router, user_group_router, admin_router)
    for router in routers:
        dp.include_router(router)


async def on_startup() -> None:
    """Действия при запуске бота"""
    logger.info("Инициализация базы данных...")
    await create_db()  # Создание таблиц в БД

    logger.info("Установка команд бота...")
    await bot.set_my_commands(commands=BOT_COMMANDS)
    # Регистрация команд в интерфейсе


async def on_shutdown() -> None:
    """Действия при завершении работы бота"""
    logger.info("Очистка ресурсов...")
    await dp.storage.close()  # Закрытие хранилища
    await bot.session.close()  # Закрытие сессии бота


async def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Запуск бота...")

    register_routers()  # Подключение обработчиков

    # Регистрация обработчиков жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Подключение middleware для работы с БД
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    try:
        # Очистка веб хуков и запуск long polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
            ],  # Обрабатываемые типы обновлений
            close_bot_session=False,  # Не закрываем сессию бота автоматически
        )
    except asyncio.CancelledError:
        logger.info("Запрос на остановку бота")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
    finally:
        await on_shutdown()  # Гарантированная очистка ресурсов


if __name__ == "__main__":
    try:
        # Запуск асинхронного event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получено прерывание с клавиатуры")
