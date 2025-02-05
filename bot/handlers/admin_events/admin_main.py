from aiogram import Router, types
from aiogram.filters import Command

# Импортируем фильтры для типов чатов и проверки администратора
from filters.chat_types import ChatTypeFilter, IsAdmin

# Импорт клавиатуры
from keyboards.reply import get_keyboard

# Создаем роутер для работы с администраторами
admin_router = Router()

# Устанавливаем фильтр для работы только в личных сообщениях и только для администраторов
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# Клавиатура для администратора (главное меню)
ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)

# Handler команды /admin для входа в функционал администратора
@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)
