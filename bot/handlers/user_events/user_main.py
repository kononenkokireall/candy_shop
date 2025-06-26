import logging
import os

from aiogram import types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto, FSInputFile, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_cart import orm_add_to_cart
from database.orm_querys.orm_query_user import orm_add_user
from filters.chat_types import ChatTypeFilter
from handlers.menu_events.menu_processing_get import get_menu_content
from handlers.user_events.user_checkout import checkout
from keyboards.inline_main import MenuCallBack
from utilit.config import settings
from utilit.metrics import start_command_errors, start_command_counter, \
    start_command_duration
from utilit.notification import NotificationService

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Обработчик команды /start. Инициализирует сессию пользователя.
@user_private_router.message(CommandStart())
async def start_cmd(
        message: types.Message,
        session: AsyncSession,  # получаем из middleware
) -> None:
    start_command_counter.inc()

    if not message.from_user:
        logger.error("Отсутствует from_user")
        start_command_errors.inc()
        await message.answer("Ошибка авторизации")
        return

    user_id = message.from_user.id

    with start_command_duration.time():
        try:
            media, kb = await get_menu_content(
                session=session,
                level=0,
                menu_name="main",
                user_id=user_id,
            )

            if media is None or kb is None:
                raise RuntimeError("get_menu_content вернул None")

            # --- отправляем пользователю ---
            if isinstance(media, InputMediaPhoto):
                await message.answer_photo(
                    photo=media.media, caption=media.caption, reply_markup=kb
                )
            else:  # Fallback: строка-file_id, документ и т.д.
                await message.answer_photo(media, reply_markup=kb)

        except Exception as e:
            logger.error("Ошибка /start: %s", e, exc_info=True)
            start_command_errors.inc()
            await message.answer(
                "Произошла внутренняя ошибка. Попробуйте позже.")


# Показывает справку по использованию бота.
@user_private_router.message(Command("help"))
async def help_cmd(message: types.Message) -> None:
    """
    Отправляет пользователю информацию о том, как пользоваться ботом-магазином.
    """
    help_text = (
        "🛍 ** CBDS_Candies 🍭 приветствует Вас!**\n"
        "Колпаки для курения и конфеты из Амстердама! 🍬\n\n"

        "📌 **Основные команды:**\n"
        "➖ /start – Запуск бота и просмотр меню.\n"
        "➖ /help – Получить справку. ℹ️\n\n"

        "📦 **Доставка:**\n"
        "Доступны разные способы. 🚚 Детали обсуждаются при заказе.\n\n"

        "💳 **Оплата:**\n"
        "Перевод на карту BLIK, TON-кошелек или наличные при встрече. 💰\n\n"

        "🏪 **О магазине:**\n"
        "Мы предлагаем качественные товары по отличным ценам! ❤️\n\n"

        "🛒 **Корзина:**\n"
        "Добавляйте, удаляйте товары и оформляйте заказ в любое время. 🔄\n\n"

        "🍬 **Товары:**\n"
        "🍭 *Cannabis Lollipops* – леденцы с разными вкусами.\n"
        "🥦💨 *Колпаки* – стильные аксессуары для вечеринок.\n\n"

        "📩 **Оформить заказ:**\n"
        "Нажмите «Оформить заказ» и напишите админу для уточнения деталей. @CBDS_support\n\n"

        "❓ Остались вопросы? Обращайтесь в поддержку! 💬"
    )
    await message.answer(help_text)


# Добавляет товар в корзину пользователя.
async def add_to_cart(callback: types.CallbackQuery,
                      callback_data: MenuCallBack,
                      session: AsyncSession
                      ) -> None:
    user_local = callback.from_user
    if user_local is None:
        await callback.answer("Ошибка: не удалось определить пользователя.",
                              show_alert=True)
        return

    try:
        # Управляем транзакцией внутри функции
        # async with session.begin():
        # Регистрируем или обновляем пользователя
        await orm_add_user(session, user_id=user_local.id,
                           first_name=user_local.first_name,
                           last_name=user_local.last_name or "",
                           phone=None)

        if callback_data.product_id is not None:
            await orm_add_to_cart(session, user_id=user_local.id,
                                  product_id=callback_data.product_id)
            await callback.answer("Товар добавлен в корзину!")
        else:
            await callback.answer(
                "Ошибка: отсутствует идентификатор товара.",
                show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}",
                     exc_info=True)
        await callback.answer(
            "Произошла ошибка при добавлении товара в корзину.",
            show_alert=True)


# Главный обработчик callback-запросов для навигации по меню.
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
        callback: CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
        notification_service: NotificationService | None = None,
) -> None:

    user_id = callback.from_user.id if callback.from_user else None
    if not user_id:
        logger.error("Callback без пользователя")
        await callback.answer("Ошибка авторизации", show_alert=True)
        return

    notification_service = notification_service or NotificationService(
        bot=callback.bot,
        admin_chat_id=settings.ADMIN_CHAT_ID,
    )

    try:
        # ------------------- checkout --------------------------------------
        if callback_data.menu_name == "checkout" and callback_data.level == 4:
            await callback.answer("⏳ Готовим заказ…")

            try:
                media, kb = await checkout(
                    session, user_id, notification_service
                )
            except ValueError as e:  ### <--- NEW
                # Нормальная бизнес-ошибка (нет товара, и т.д.)
                await callback.message.answer(str(e))  # показываем текст
                await callback.answer()
                return

            if not callback.message:
                await callback.answer("Сообщение недоступно", show_alert=True)
                return

            if isinstance(media, str) and os.path.isfile(media):  ### <--- NEW
                media = InputMediaPhoto(media=FSInputFile(media))

            try:
                await callback.message.edit_media(media=media, reply_markup=kb)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    await callback.answer("Корзина актуальна", show_alert=True)
                else:
                    raise
            finally:
                await callback.answer()
            return

        # ------------------- add_to_cart -----------------------------------
        if callback_data.menu_name == "add_to_cart":
            await add_to_cart(callback, callback_data, session)
            await callback.answer()
            return

        # ------------------- обычная навигация -----------------------------
        message = callback.message
        if not message:
            await callback.answer("Сообщение недоступно", show_alert=True)
            return

        page = callback_data.page or 1

        media, new_markup = await get_menu_content(
            session,
            level=callback_data.level,
            menu_name=callback_data.menu_name,
            category=callback_data.category,
            page=page,
            user_id=user_id,
            product_id=callback_data.product_id,
        )
        if media is None:                                        ### <--- NEW
            await message.edit_reply_markup(reply_markup=new_markup)
            await callback.answer()
            return

        # --------- приводим media к InputMediaPhoto ------------------------
        if isinstance(media, str):
            if os.path.isfile(media):  # локальный файл
                media = InputMediaPhoto(media=FSInputFile(media))
            else:  # URL или file_id
                media = InputMediaPhoto(media=media)
        elif not isinstance(media, InputMediaPhoto):
            await callback.answer("Неподдерживаемый тип медиа",
                                  show_alert=True)
            return

        try:
            await message.edit_media(media=media, reply_markup=new_markup)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.debug("Сообщение не изменено: %s", e)
            else:
                logger.error("Ошибка edit_media: %s", e, exc_info=True)
                await callback.answer("Ошибка обновления", show_alert=True)
        else:
            await callback.answer()

    except Exception as e:
        logger.error("Критическая ошибка user_menu: %s", e, exc_info=True)
        await callback.answer("Ошибка обработки запроса", show_alert=True)
