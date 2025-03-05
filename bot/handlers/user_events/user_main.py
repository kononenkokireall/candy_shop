import logging
from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import InputMediaPhoto

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_cart import orm_add_to_cart
from database.orm_querys.orm_query_user import orm_add_user

# Импортируем пользовательские фильтры и вспомогательные модули
from filters.chat_types import ChatTypeFilter

from handlers.menu_events.menu_processing_get import get_menu_content
from handlers.user_events.user_checkout import checkout

from keyboards.inline_main import MenuCallBack
from utilit.config import settings
from utilit.notification import NotificationService

# Создаем маршрутизатор для работы с маршрутами пользователя
user_private_router = Router()

# Указываем, что маршруты этого маршрутизатора применимы только для личных чатов
user_private_router.message.filter(ChatTypeFilter(["private"]))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


##############################Handler команды /start для пользователя##################################################

# Handler для обработки команды /start
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    # Получаем контент главного меню из базы данных
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    # Посылаем пользователю фотографию с заданным описанием и клавиатурой
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


#########################Handler обработки добавления товара в корзину для пользователя################################

# Функция добавления товара в корзину
async def add_to_cart(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession
):
    user_local = callback.from_user  # Получаем информацию о пользователе
    # Добавляем пользователя в базу данных
    await orm_add_user(
        session,
        user_id=user_local.id,
        first_name=user_local.first_name,
        last_name=user_local.last_name,
        phone=None,
    )
    # Добавляем товар в корзину
    await orm_add_to_cart(session, user_id=user_local.id, product_id=callback_data.product_id)
    # Отправляем уведомление пользователю
    await callback.answer("Товар добавлен в корзину!")


##################################Handler обработки меню для пользователя##############################################

# Handler для обработки пользовательского меню на основе данных MenuCallBack
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
        notification_service: NotificationService = None
):
    """
        Обработчик меню пользователя.

        Args:
            callback: CallbackQuery от Telegram.
            callback_data: Данные callback, parsing через MenuCallBack.
            session: Асинхронная сессия SQLAlchemy.
            notification_service: Сервис уведомлений.
        """
      # Если сервис уведомлений не передан, создаём его
    if notification_service is None:
        notification_service = NotificationService(
            bot=callback.bot,  # или другой способ получения объекта бота
            admin_chat_id=settings.ADMIN_CHAT_ID
          )

    try:
        # Инициализация сервиса уведомлений, если он не передан
        # Обработка действия "checkout"
        if callback_data.menu_name == "checkout" and callback_data.level == 4:
            media, keyboards = await checkout(session, callback.from_user.id, notification_service)
            await callback.message.edit_media(media=media, reply_markup=keyboards)
            await callback.answer()
            return  # Завершаем выполнение, чтобы избежать дублирования

        # Обработка действия "add_to_cart"
        if callback_data.menu_name == "add_to_cart":
            await add_to_cart(callback, callback_data, session)
            return  # Завершаем выполнение, чтобы избежать дублирования
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
        # Проверяем, что media и reply_markup корректны
        if not media:
            await callback.answer("Медиа не найдено.", show_alert=True)
            return

        # Если media — это строка, оборачиваем её в InputMediaPhoto
        if isinstance(media, str):
            media = InputMediaPhoto(media=media)

        # Лог данные для отладки
        logger.debug(f"Media: {media}")
        logger.debug(f"Reply Markup: {reply_markup}")

        # Обновляем содержимое сообщения с новым медиа и клавиатурой
        try:
            await callback.message.edit_media(media=media, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка при изменении медиа: {e}", exc_info=True)
            await callback.answer("Произошла ошибка при обновлении медиа.", show_alert=True)

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в обработчике user_menu: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса.", show_alert=True)