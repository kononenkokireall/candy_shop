from aiogram import F, types, Router
from aiogram.filters import CommandStart


from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_to_cart, orm_add_user


from filters.chat_types import ChatTypeFilter
from keyboards.inline import get_callback_btn


router = Router()
router.message.filter(ChatTypeFilter(["private"]))


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
    "Приветствуем вас в нашем магазине! 🎉 Здесь вас ждут уникальные товары высокого качества,"
    " которые сочетают в себе стиль, незабываемый вкус и современные технологии."
    " 🍭✨ Готовы открыть для себя что-то удивительное и полезное?"
    " Давайте начнём ваше путешествие к идеальной покупке! 🛒",
        reply_markup=get_callback_btn(btn={
            'Нажми здесь': 'some_1',
        }))

@router.callback_query(F.data.startwith('some_'))
async def counter(callback: types.CallbackQuery):
    number = int(callback.data.split('_')[-1])

    await callback.message.edit_text(
        text=f"Нажатый - {number}",
        reply_markup=get_callback_btn(btn={
            'Нажми еще раз': f'some_{number+1}'
        })
    )