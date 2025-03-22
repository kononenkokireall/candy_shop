from aiogram.filters import Filter
from aiogram import Bot, types


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        # Добавляем проверку на наличие from_user
        if message.from_user is None:
            return False
        return message.from_user.id in bot.my_admins_list
