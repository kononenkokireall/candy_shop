from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto
from data.help_data import HELP_TEXT, HELP_IMAGES


router = Router()


@router.message(lambda message: message.text.lower() == "помощь")
async def user_help(message: Message):
    """
    Функция вызова поддержки бота
    """
    await message.answer("Добро пожаловать в раздел помощи! Вот основные темы:")

    for section, text in HELP_TEXT.items():
        photo_path = HELP_IMAGES(section)
        if photo_path:
            try:
                with open(photo_path, 'rb') as photo:
                    await message.answer_photo(
                        photo=photo, caption=text
                    )
            except FileNotFoundError:
                await message.answer("Извините, произошла ошибка при загрузке изображения.")
        else:
            await message.answer(text)

    await message.answer("""Если у вас остались вопросы,
                         напишите в  тех.поддержку(ссылка на чат)""")
