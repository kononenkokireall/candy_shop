import logging
from typing import Optional

from aiogram import types, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from cache.invalidator import CacheInvalidator
from database.orm_querys.orm_query_cart import orm_add_to_cart
from database.orm_querys.orm_query_user import orm_add_user
from filters.chat_types import ChatTypeFilter
from handlers.menu_events.menu_processing_get import get_menu_content
from handlers.user_events.user_checkout import checkout
from keyboards.inline_main import MenuCallBack
from utilit.config import settings
from utilit.notification import NotificationService

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Обработчик команды /start. Инициализирует сессию пользователя.
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession) -> None:
    if not message.from_user:
        logger.error("Отсутствует информация о пользователе в message")
        await message.answer("Ошибка авторизации", show_alert=True)
        return

    user_id = message.from_user.id

    try:
        # Получаем медиа и клавиатуру
        media, reply_markup = await get_menu_content(session, level=0,
                                                     menu_name="main",
                                                     user_id=user_id,
                                                     )

        # Проверяем, что полученные значения корректны
        if media is None or reply_markup is None:
            logger.error("Не удалось получить медиа или клавиатуру для /start")
            await message.answer("Ошибка загрузки меню. Попробуйте позже.")
            return

        # Проверяем, что media является InputMediaPhoto, и обрабатываем его
        if isinstance(media, InputMediaPhoto):
            await message.answer_photo(media.media, caption=media.caption,
                                       reply_markup=reply_markup)
        else:
            logger.error(f"Неверный тип медиа: {type(media)}")
            await message.answer("Ошибка загрузки медиа. Попробуйте позже.")

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}",
                     exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке команды. Попробуйте позже.")


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

    await orm_add_user(session, user_id=user_local.id,
                       first_name=user_local.first_name,
                       last_name=user_local.last_name or "", phone=None)

    if callback_data.product_id is not None:
        await orm_add_to_cart(session, user_id=user_local.id,
                              product_id=callback_data.product_id)
        await callback.answer("Товар добавлен в корзину!")
        await session.commit()
    else:
        await callback.answer("Ошибка: отсутствует идентификатор товара.",
                              show_alert=True)


# Главный обработчик callback-запросов для навигации по меню.
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
        notification_service: Optional[NotificationService] = None
) -> None:
    # Проверка наличия информации о пользователе
    if callback.from_user is None:
        logger.error("Callback не содержит информации о пользователе")
        await callback.answer("Ошибка авторизации", show_alert=True)
        return

    # Инициализация сервиса уведомлений при необходимости
    if notification_service is None:
        notification_service = NotificationService(
            bot=callback.bot,
            admin_chat_id=settings.ADMIN_CHAT_ID
        )

    try:
        # Обработка специального случая для чек аута
        if callback_data.menu_name == "checkout" and callback_data.level == 4:
            media, keyboards = await checkout(
                session,
                callback.from_user.id,
                notification_service
            )

            # Проверяем тип и наличие сообщения
            message = callback.message
            if not isinstance(message, types.Message):
                await callback.answer(
                    "Ошибка: сообщение недоступно!",
                    show_alert=True
                )
                return

                # Проверяем наличие фото
            if not message.photo:
                await callback.answer(
                    "Сообщение не содержит фото!",
                    show_alert=True
                )
                return

            try:
                await callback.message.edit_media(media=media,
                                                  reply_markup=keyboards)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    await callback.answer("Корзина уже актуальна",
                                          show_alert=True)
                else:
                    raise
            finally:
                await callback.answer()
            return

        # Обработка добавления в корзину
        if callback_data.menu_name == "add_to_cart":
            await add_to_cart(callback, callback_data, session)
            return

            # Инвалидация кеша для баннеров при их запросе
        if callback_data.menu_name == "banner":
            logger.debug(
                f"Инвалидируем кеш для баннера: banner:{callback_data.page}")
            await CacheInvalidator.invalidate([
                f"banner:{callback_data.page}",
                f"menu:*{callback_data.page}*"
            ])

        # Основная логика обработки меню --------------------------------------

        # Получаем текущее состояние сообщения ПЕРЕД генерацией нового контента
        current_message = callback.message
        if not isinstance(current_message, types.Message):
            await callback.answer(
                "Ошибка: текущее сообщение недоступно!",
                show_alert=True
            )
            return

            # Извлекаем данные из сообщения
        original_media = (current_message.photo[-1].file_id
                          if current_message.photo
                          else None
                          )
        original_reply_markup = current_message.reply_markup

        # Генерация нового контента
        media, reply_markup = await get_menu_content(
            session,
            level=callback_data.level,
            menu_name=callback_data.menu_name,
            category=callback_data.category,
            page=callback_data.page,
            user_id=callback.from_user.id,
            product_id=callback_data.product_id
        )

        # Валидация медиа
        if media is None:
            await callback.answer("Медиа не найдено.", show_alert=True)
            return

        if isinstance(media, str):
            media = InputMediaPhoto(media=media)
        elif not isinstance(media, InputMediaPhoto):
            await callback.answer("Неподдерживаемый тип медиа.",
                                  show_alert=True)
            return

            # Проверяем изменения
        is_media_changed = (isinstance(media, InputMediaPhoto) and
                            media.media != original_media
                            )
        is_markup_changed = str(reply_markup) != str(original_reply_markup)

        # Если ничего не изменилось - отправляем ответ и выходим
        if not is_media_changed and not is_markup_changed:
            await callback.answer("Сообщение уже актуально.",
                                  show_alert=True)
            return

        # Попытка обновления сообщения
        try:

            await callback.message.edit_media(
                media=media,
                reply_markup=reply_markup
            )
        except TelegramBadRequest as e:
            # Обработка конкретной ошибки "неизмененного сообщения"
            if "message is not modified" in str(e):
                logger.warning(f"Игнорируем неизмененное сообщение: {e}")
                await callback.answer()
            else:
                logger.error(f"Ошибка редактирования медиа: {e}",
                             exc_info=True)
                await callback.answer("Ошибка обновления контента",
                                      show_alert=True)
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
            await callback.answer("Произошла непредвиденная ошибка",
                                  show_alert=True)
        finally:
            await callback.answer()

    except Exception as e:
        logger.error(f"Критическая ошибка в обработчике меню: {e}",
                     exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса.",
                              show_alert=True)
