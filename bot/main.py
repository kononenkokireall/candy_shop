"""
Основной модуль Telegram-бота.
Организация работы бота, роутинга и взаимодействия с базой данных.
"""
import asyncio
import logging
from typing import Final, List

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, User as TgUser
from redis.asyncio import Redis

from database.engine import session_maker, create_db
from handlers.admin_events.admin_main import admin_router
from handlers.user_events.user_group import user_group_router
from handlers.user_events.user_main import user_private_router
from middlewares.db import DataBaseSession
from utilit.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logging.getLogger("aiogram").setLevel(logging.WARNING)

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
    routers = (user_private_router, user_group_router, admin_router)
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

    await create_db()
    await bot.set_my_commands(commands=BOT_COMMANDS)

    try:
        bot.redis = await connect_redis()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect Redis: {e}")
        bot.redis = None

async def on_shutdown() -> None:
    logger.info("Shutting down...")

    if bot.redis:
        await bot.redis.aclose()

    await dp.storage.close()
    await bot.session.close()

async def main() -> None:
    register_routers()
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

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
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")