import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, types  # Импорты библиотек aiogram для работы с ботом
from aiogram.client.default import DefaultBotProperties  # Настройки бота по умолчанию
from aiogram.enums import ParseMode  # Режим форматирования сообщений (HTML, Markdown)

from dotenv import find_dotenv, load_dotenv  # Для загрузки переменных окружения из файла .env

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Загрузка переменных окружения из .env файла
load_dotenv(find_dotenv())

from middlewares.db import DataBaseSession  # Middleware для работы с базой данных
from database.engine import create_db, drop_db, session_maker  # Инструменты для управления БД

from handlers.user_private import user_private_router  # Маршрутизация для приватных чатов пользователя
from handlers.user_group import user_group_router  # Маршрутизация для групповых чатов
from handlers.admin_private import admin_router  # Маршрутизация для чатов администратора

# Создание объекта бота с использованием токена из переменных окружения и настройкой parse_mode
bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.my_admins_list = []  # Пустой список для ID администраторов (можно заполнить при необходимости)

# Создание диспетчера для управления обработкой обновлений
dp = Dispatcher()

# Регистрация маршрутов обработчиков
dp.include_router(user_private_router)  # Обработчики для приватных чатов
dp.include_router(user_group_router)  # Обработчики для групповых чатов
dp.include_router(admin_router)  # Обработчики для админских чатов


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
        # await drop_db()
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
    print('бот лег')  # Дополнительный вывод, можно заменить на логирование


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
    dp.startup.register(on_startup)  # Регистрация функции запуска
    dp.shutdown.register(on_shutdown)  # Регистрация функции завершения

    logging.info("Добавление middleware для работы с базой данных...")
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.info("Удаление вебхуков (если были установлены)...")
    await bot.delete_webhook(drop_pending_updates=True)

    # Настройка команд бота (раскомментировать, если требуется)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())  # Удаление существующих команд
    # await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())  # Установка новых команд

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
