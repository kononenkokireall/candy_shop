# handlers/user_events/cart_handlers.py

import logging
from typing import Optional

from aiogram import F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from aiogram.types import Message, InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_cart import orm_reduce_product_in_cart, \
    orm_full_remove_from_cart
from handlers.menu_events.menu_process_cart import carts
from handlers.user_events.user_main import user_private_router
from keyboards.inline_main import MenuCallBack

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



@user_private_router.callback_query(MenuCallBack.filter(F.menu_name == "decrement"))
async def decrement_product(
        callback: CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession
) -> None:
    if not callback_data.product_id:
        await callback.answer("Ошибка товара!")
        return

    changed = await orm_reduce_product_in_cart(
        session=session,
        user_id=callback.from_user.id,
        product_id=callback_data.product_id
    )

    if changed and callback.message:
        await update_cart_message(callback.message, session)
    else:
        await callback.answer("Минимальное количество: 1 шт")

    await callback.answer()


@user_private_router.callback_query(MenuCallBack.filter(F.menu_name == "delete"))
async def delete_product(
        callback: CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession
) -> None:
    if not callback_data.product_id:
        await callback.answer("Ошибка товара!")
        return

    removed = await orm_full_remove_from_cart(
        session=session,
        user_id=callback.from_user.id,
        product_id=callback_data.product_id
    )

    if removed and callback.message:
        await update_cart_message(callback.message, session)
    else:
        await callback.answer("Товар не найден!")

    await callback.answer()


async def update_cart_message(
    message: Message,
    session: AsyncSession,
    bot: Optional[Bot] = None
) -> None:
    """Обновляет сообщение с корзиной после изменений"""
    if message.from_user is None:
        logger.warning("message.from_user is None, невозможно получить ID пользователя.")
        return

    media: Optional[InputMediaPhoto] = None
    keyboard: Optional[InlineKeyboardMarkup] = None

    try:
        media, keyboard = await carts(
            user_id=message.from_user.id,
            session=session,
            level=1,
            menu_name="default",
            page=1,
            product_id=0
        )

        if media is not None:
            await message.edit_media(media=media, reply_markup=keyboard)
        else:
            logger.warning("media is None, пропускаем edit_media")

    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif "message to edit not found" in str(e) and bot:
            if media is not None:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=media.media,
                    reply_markup=keyboard if keyboard else None
                )
            else:
                logger.warning("media is None, невозможно отправить фото")
        else:
            logger.error(f"Ошибка обновления корзины: {e}")
