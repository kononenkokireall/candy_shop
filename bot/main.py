import asyncio
import os
import logging

# Импорты библиотек aiogram для работы с ботом
from aiogram import Bot, Dispatcher, types
# Настройки бота по умолчанию
from aiogram.client.default import DefaultBotProperties
# Режим форматирования сообщений (HTML, Markdown)
from aiogram.enums import ParseMode

# Для загрузки переменных окружения из файла .env
# from dotenv import find_dotenv, load_dotenv
from utilit.config import settings

# Middleware для работы с базой данных
from middlewares.db import DataBaseSession
# Инструменты для управления БД
from database.engine import create_db, drop_db, session_maker

# Маршрутизация для приватных чатов пользователя
from handlers.user_events.user_main import user_private_router
# Маршрутизация для групповых чатов
from handlers.user_events.user_group import user_group_router
# Маршрутизация для чатов администратора
from handlers.admin_events.admin_main import admin_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Загрузка переменных окружения из .env файла
# load_dotenv(find_dotenv())
# Создание объекта бота с использованием токена из переменных окружения и настройкой parse_mode
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# Пустой список для ID администраторов (можно заполнить при необходимости)
bot.my_admins_list = []

# Создание диспетчера для управления обработкой обновлений
dp = Dispatcher()

# Регистрация маршрутов обработчиков
# Обработчики для приватных чатов
dp.include_router(user_private_router)
# Обработчики для групповых чатов
dp.include_router(user_group_router)
# Обработчики для админских чатов
dp.include_router(admin_router)


async def on_startup(bot: Bot):
    """
    Действия при запуске бота.
    Эта функция вызывается автоматически при старте. Здесь выполняется инициализация базы данных.
    Args:
        bot (Bot): Объект бота.
    """
    logging.info("Запуск бота и инициализация базы данных...")
    try:
        # Если требуется удалить базу данных, раскомментируйте следующую строку
        #await drop_db()
        await create_db()
        logging.info("База данных успешно создана.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)


async def on_shutdown(bot: Bot):
    """
    Действия при завершении работы бота.
    Здесь можно реализовать освобождение ресурсов или другие завершающие действия.
    Args:
        bot (Bot): Объект бота.
    """
    logging.info("Завершение работы бота. Освобождение ресурсов...")
    print('Бот завершил роботу.')  # Дополнительный вывод, можно заменить на логирование


async def main():
    """
    Основная функция запуска бота.
    Включает следующие этапы:
    - Регистрация функций запуска и завершения.
    - Подключение middleware для работы с базой данных.
    - Удаление вебхуков (если были установлены) для использования long polling.
    - Запуск long polling для обработки поступающих обновлений.
    """
    logging.info("Регистрация функций старта и остановки бота...")
    # Регистрация функции запуска
    dp.startup.register(on_startup)
    # Регистрация функции завершения
    dp.shutdown.register(on_shutdown)

    logging.info("Добавление middleware для работы с базой данных...")
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.info("Удаление вебхуков (если были установлены)...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Настройка команд бота (раскомментировать, если требуется)

    # Удаление существующих команд
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())

    # Установка новых команд
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())

    logging.info("Запуск long polling для обработки входящих обновлений...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logging.error(f"Ошибка в процессе polling: {e}", exc_info=True)


# Запуск основного события asyncio
if __name__ == '__main__':
    logging.info("Запуск основного цикла приложения...")
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Ошибка запуска приложения: {e}", exc_info=True)