from aiogram import types, Router

from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

# Импортируем пользовательские фильтры и вспомогательные модули
from filters.chat_types import ChatTypeFilter
from handlers.menu_events.menu_main import get_menu_content

# Загружаем переменные окружения (например, ADMIN_ID)
load_dotenv()

# Создаем маршрутизатор для работы с маршрутами пользователя
user_private_router = Router()

# Указываем, что маршруты этого маршрутизатора применимы только для личных чатов
user_private_router.message.filter(ChatTypeFilter(["private"]))


# Handler для обработки команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # Получаем контент главного меню из базы данных
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    # Посылаем пользователю фотографию с заданным описанием и клавиатурой
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)