from aiogram import Bot

class NotificationService:
    def __init__(self, bot: Bot, admin_chat_id: int):
        self.bot = bot
        self.admin_chat_id = admin_chat_id


    async def send_to_admin(self, text: str, **kwargs):
        """Отправляет сообщение администратору"""
        await self.bot.send_message(
            chat_id=self.admin_chat_id,
            text=text,
            **kwargs
        )
