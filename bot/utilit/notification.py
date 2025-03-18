from typing import Any

from aiogram import Bot


class NotificationService:
    """
    Сервис для отправки уведомлений через Telegram бота.

    Attributes:
        bot: Экземпляр Telegram бота для отправки сообщений
        admin_chat_id: ID чата администратора для получения уведомлений
    """

    def __init__(self, bot: Bot, admin_chat_id: int) -> None:
        """
        Инициализация сервиса уведомлений.

        Args:
            bot: Экземпляр aiogram Bot
            admin_chat_id: Числовой идентификатор чата администратора
                           (можно получить через @userinfo)
        """
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    async def send_to_admin(self, text: str, **kwargs: Any) -> None:
        """
        Асинхронная отправка сообщения администратору.

        Args:
            text: Текст сообщения для отправки
            **kwargs: Дополнительные аргументы для bot.send_message():
                      parse_mode, disable_web_page_preview и т.д.

        Examples:
            await service.send_to_admin("Новый заказ!", parse_mode="HTML")
        """
        await self.bot.send_message(chat_id=self.admin_chat_id,
                                    text=text, **kwargs)
