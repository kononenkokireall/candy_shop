from aiogram.types import InputMediaPhoto
# Импортируем запросы ORM для работы с базой данных
from database.orm_querys.orm_query_banner import orm_get_banner
# Импортируем модули для создания клавиатуры
from keyboards.inline_main import get_user_main_btn

# Функция создания главного меню
async def main_menu(session, level, menu_name):
    # Получаем баннер из базы данных для заданного меню
    banner = await orm_get_banner(session, menu_name)
    # Подготавливаем изображение для отправки пользователю
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    # Генерируем клавиатуру для главного меню
    keyboards = get_user_main_btn(level=level)
    return image, keyboards
