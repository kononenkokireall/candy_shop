from aiogram import Bot
from utilit.config import settings

class NotificationService:
    def __init__(self, bot: Bot, admin_chat_id: int):
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    async def send_to_admin(self, text: str, **kwargs):
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            **kwargs
        )


def get_notification_service() -> NotificationService:
    bot_token = settings.BOT_TOKEN
    admin_chat_id = settings.ADMIN_CHAT_ID
    bot = Bot(token=bot_token)
    return NotificationService(bot, admin_chat_id)
