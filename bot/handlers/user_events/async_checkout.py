import logging

from aiogram import Bot

from database.engine import session_maker
from utilit.config import settings
from utilit.notification import NotificationService
from .user_checkout import checkout  # ваша «тяжёлая» функция

logger = logging.getLogger(__name__)


async def process_checkout(
        bot: Bot,
        chat_id: int,
        message_id: int,
        user_id: int,
) -> None:
    # отдельная сессия на задачу
    async with session_maker() as session:
        media, kb = await checkout(
            session=session,
            user_id=user_id,
            notification_service=NotificationService(
                bot=bot,
                admin_chat_id=settings.ADMIN_CHAT_ID,   # ← добавили
            ),
        )

    # пробуем заменить медиа-картинку корзины на «Спасибо за заказ»
    try:
        await bot.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=media,
            reply_markup=kb,
        )
    except Exception as e:
        logger.error("Не смог отредактировать сообщение: %s", e)