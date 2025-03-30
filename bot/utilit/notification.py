import logging
from typing import Any, Optional

from aiogram import Bot

# Сервис для отправки уведомлений через Telegram бота.
class NotificationService:
    """
    Сервис для отправки уведомлений через Telegram бота.
    Attributes:
        bot: Экземпляр Telegram бота для отправки сообщений
        admin_chat_id: ID чата администратора для получения уведомлений
    """

    def __init__(self,
                 admin_chat_id: int,
                 bot: Optional[Bot] = None,
                 ) -> None:
        """
        Инициализация сервиса уведомлений.
        Args:
            bot: Экземпляр aiogram Bot
            admin_chat_id: Числовой идентификатор чата администратора
                           (можно получить через @userinfo)
        """
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    async def send_to_admin(self, text: str, **kwargs: Any) -> bool:
        """
        Отправляет сообщение администратору, если бот доступен.
        Returns:
            bool: Успешность отправки (True/False)
        Raises:
            ValueError: Если бот не инициализирован
        """
        if not self.bot:
            logging.warning("Bot не доступен для отправки уведомления!")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=text,
                **kwargs
            )
            return True
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления: {str(e)}")
            return False

    def set_bot(self, bot: Bot) -> None:
        """Динамическая установка бота"""
        self.bot = bot
