from string import punctuation  # Подключаем модуль для работы с пунктуацией

from aiogram import Bot, types, Router
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter
# Фильтр типов чатов (группы, супергруппы)
from common.restricted_words import restricted_words

# Список запрещенных слов

# Создаем роутер для обработки сообщений
# и событий в чатах с типами "group" и "supergroup"
user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))
# Фильтруем только групповые чаты
user_group_router.edited_message.filter(
    ChatTypeFilter(["group", "supergroup"]))


# Handler для команды "/admin"
@user_group_router.message(Command("admin"))
async def get_admins(
        message: types.Message,
        bot: Bot
) -> None:
    """
    Когда пользователь в чате вводит команду "/admin",
    бот получает список администраторов чата и сохраняет их ID.
    Также он удаляет сообщение, если его отправил администратор.
    """
    chat_id = message.chat.id  # ID текущего чата
    admins_list = await bot.get_chat_administrators(chat_id)
    # Получаем список администраторов чата
    # print(admins_list)
    # (Можно раскомментировать для отладки:
    # вывести список всех администраторов и их данные)

    # Генератор списка: выбираем только администраторов и создателя чата
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    # Сохраняем список идентификаторов администраторов в атрибуте `bot`

    # Если сообщение отправлено администратором, удаляем его
    # Явная проверка на None
    if message.from_user is not None and message.from_user.id in bot.my_admins_list:
        await message.delete()

    # print(admins_list)
    # (Можно раскомментировать для отладки:
    # вывести список идентификаторов администраторов)


# Функция для очистки текста от пунктуации
def clean_text(text: str) -> str:
    """
    Удаляет все символы пунктуации из переданного текста.
    """
    return text.translate(str.maketrans("", "", punctuation))
    # Убираем знаки пунктуации из текста


# Handler для обработки как новых,
# так и отредактированных сообщений в группах/супергруппах
@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message) -> None:
    """
    Фильтрует сообщения, содержащие запрещенные слова.
    Отправляет предупреждение пользователю и удаляет сообщение.
    """
    if message.text is None:
        return
    text = message.text.lower()
    cleaned_text = clean_text(text).split()

    if restricted_words.intersection(cleaned_text):
        # Безопасное получение имени пользователя
        user_name = (
            message.from_user.full_name
            if message.from_user is not None
            else "Пользователь"
        )

        await message.answer(f"{user_name}, соблюдайте порядок в чате!")
        await message.delete()

        # ВАЖНО: Код ниже можно раскомментировать,
        # чтобы автоматически банить пользователей
        # за использование запрещенных слов
        # await message.chat.ban(message.from_user.id)
