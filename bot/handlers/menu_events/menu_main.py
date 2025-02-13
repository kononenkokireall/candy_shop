from aiogram.types import InputMediaPhoto

# Импортируем запросы ORM для работы с базой данных
from database.orm_querys.orm_query_banner import orm_get_banner


# Импортируем модули для создания клавиатуры
from keyboards.inline_main import get_user_main_btn


async def main_menu(session, level, menu_name):
    # try:
        # Получаем баннер из базы данных для заданного меню
        banner = await orm_get_banner(session, menu_name)
        # if not banner or not banner.image:
        #     raise ValueError("Баннер не найден или отсутствует изображение.")
        #
        # # Проверяем, что URL изображения корректен
        # if not banner.image.startswith(("http://", "https://")):
        #     raise ValueError("Некорректный URL изображения.")

        # Подготавливаем изображение для отправки пользователю
        image = InputMediaPhoto(media=banner.image, caption=banner.description)

        # Генерируем клавиатуру для главного меню
        keyboards = get_user_main_btn(level=level)

        return image, keyboards
    # except Exception as e:
    #     print("Ошибка в main_menu:", e)
    #     return None, None