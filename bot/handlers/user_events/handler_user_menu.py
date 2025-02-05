from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.menu_events.menu_main import get_menu_content
from handlers.user_events.user_add_cart import add_to_cart
from handlers.user_events.user_main import user_private_router
from keyboards.inline_main import MenuCallBack


# Handler для обработки пользовательского меню на основе данных MenuCallBack
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    if callback_data.menu_name == "add_to_cart":  # Если действие - добавление в корзину
        await add_to_cart(callback, callback_data, session)
        return

    # Получаем контент меню из базы данных
    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        user_id=callback.from_user.id,
        product_id=callback_data.product_id,
    )
    # Обновляем содержимое сообщения с новым медиа и клавиатурой
    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
