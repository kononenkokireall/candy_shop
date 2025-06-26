"""
Основной модуль Telegram-бота.
Организация работы бота, роутинга и взаимодействия с базой данных.
"""
import asyncio
import logging
from collections import Counter
from typing import Final, List

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, User as TgUser
from redis.asyncio import Redis

from database.engine import session_maker, create_db, drop_db
from handlers.admin_events import admin_router_root
from handlers.user_events.user_group import user_group_router
from handlers.user_events.user_main import user_private_router
from prometheus_client import start_http_server, Counter, Gauge
from utilit.metrics_server import run_metrics_server
from middlewares.db import DBSessionMiddleware
from utilit.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Метрики Prometheus
BOT_STARTED = Counter("telegram_bot_started_total",
                      "Total number of times bot started")
BOT_COMMAND_START = Counter("telegram_bot_command_start_total",
                            "Total /start commands received")
REDIS_CONNECTED = Gauge("telegram_bot_redis_connected",
                        "Whether Redis is connected (1) or not (0)")

BOT_COMMANDS: Final[List[BotCommand]] = [
    BotCommand(command="start", description="Старт"),
    BotCommand(command="help", description="Помощь"),
]


class CustomBot(Bot):
    def __init__(self):
        super().__init__(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.admins: List[int] = []
        self.redis: Redis = None


bot = CustomBot()
dp = Dispatcher()


def register_routers() -> None:
    routers = (user_private_router, user_group_router, admin_router_root)
    for router in routers:
        dp.include_router(router)


async def connect_redis() -> Redis:
    try:
        return await Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            ssl_cert_reqs=None
        )
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        raise


async def on_startup() -> None:
    logger.info("Starting bot version 1.1.0")
    logger.info(f"Environment: {settings.MODE}")

    # await drop_db()
    await create_db()
    await bot.set_my_commands(commands=BOT_COMMANDS)
    BOT_STARTED.inc()
    # Запуск HTTP сервера Prometheus для экспорта метрик
    asyncio.create_task(run_metrics_server(host="0.0.0.0", port=8000))
    #await init_pool()

    try:
        bot.redis = await connect_redis()
        if bot.redis:
            REDIS_CONNECTED.set(1)
        else:
            REDIS_CONNECTED.set(0)

        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect Redis: {e}")
        bot.redis = None


async def on_shutdown() -> None:
    logger.info("Shutting down...")

    if bot.redis:
        await bot.redis.aclose()

    #await close_pool()
    await dp.storage.close()
    await bot.session.close()


async def main() -> None:
    register_routers()
    dp.update.middleware(DBSessionMiddleware(session_maker))

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            close_bot_session=False
        )
    except asyncio.CancelledError:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        if bot.admins:
            await asyncio.gather(*[
                bot.send_message(admin_id, f"🚨 Bot crashed: {e}")
                for admin_id in bot.admins
            ])
    finally:
        await on_shutdown()


if __name__ == "__main__":
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required!")

    try:
        asyncio.run(main(), debug=True)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
