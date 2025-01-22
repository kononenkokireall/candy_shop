from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command
from aiogram.utils.formatting import as_list, as_marked_section, Bold
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_products
from keyboards.reply import get_keyboard
from filters.chat_types import ChatTypeFilter
from decimal import Decimal

router = Router()
router.message.filter(ChatTypeFilter(["private"]))

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        'Привет, Инфо про магазин',
        reply_markup=get_keyboard(
            "Меню",
            "О магазине",
            "Варианты оплаты",
            "Варианты доставки",
            placeholder="Что вас интересует?",sizes=(2, 2)),
    )

@router.message(F.text.lower() == "меню")
@router.message(Command("menu"))
async def cmd_menu(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        formatted_price = product.price.quantize(Decimal('1.00'))
        await message.answer_photo(
            product.image, caption=f"<strong>{product.name}</strong>\n{product.description}\n"
                                   f"Стоимость: {formatted_price} PLN.",
        )
    await message.answer('Меню Магазина: ')


@router.message(F.text.lower() == "варианты оплаты")
@router.message(Command("payment"))
async def cmd_payment(message: types.Message):

    text = as_marked_section(
        Bold("Варианты оплаты: "),
        "BLIK номер",
        "TON Wallet",
        marker='\U0001F4B0'
    )
    await message.answer(text.as_html())


@router.message(F.text.lower() == 'варианты доставки')
@router.message(Command("shipping"))
async def cmd_menu(message: types.Message):

    text = as_list(
        as_marked_section(
        Bold("Варианты доставки: "),
        "Самовывоз",
        "Доставка на почтомат",
        marker='\U0001F4E6'
    ),
        as_marked_section(
         Bold("Не отправляем"),
            "Голуби"
        ),
        sep='\n----------------\n'
        )
    await message.answer(text.as_html())


@router.message(F.text.lower() == "о магазине")
@router.message(Command("about"))
async def cmd_about(message: types.Message):
    await message.answer('О нас: ')
