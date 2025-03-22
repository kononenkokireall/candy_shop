import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram import types, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_querys.orm_query_cart import orm_add_to_cart
from database.orm_querys.orm_query_user import orm_add_user

# Импорт пользовательских фильтров и вспомогательных модулей.
from filters.chat_types import ChatTypeFilter

# Импорт функции для получения контента меню из базы данных.
from handlers.menu_events.menu_processing_get import get_menu_content

# Импорт функции оформления заказа (checkout) для обработки заказа пользователя.
from handlers.user_events.user_checkout import checkout

# Импорт структуры данных для формирования callback-данных меню.
from keyboards.inline_main import MenuCallBack

# Импорт настроек (например, ADMIN_CHAT_ID).
from utilit.config import settings

# Импорт сервиса уведомлений для отправки сообщений администратору.
from utilit.notification import NotificationService

# Создаем маршрутизатор для обработки маршрутов,
# предназначенных для личных чатов пользователя.
user_private_router = Router()

# Фильтруем входящие сообщения,
# чтобы обрабатывать только личные (private) чаты.
user_private_router.message.filter(ChatTypeFilter(["private"]))

# Настройка базового логирования:
# устанавливаем уровень логирования и формат сообщений.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Обработчик команды /start.
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession) -> None:
    """
    Обрабатывает команду /start, получая контент главного меню из базы данных
    и отправляя его пользователю в виде фотографии с подписью и клавиатурой.
    """
    user_id = message.from_user.id
    # Получаем медиа-контент и клавиатуру для главного меню.
    media, reply_markup = await get_menu_content(session,
                                                 level=0,
                                                 menu_name="main",
                                                 user_id=user_id)

    # Добавить проверку
    if not media or not reply_markup:
        await message.answer("Ошибка загрузки меню. Попробуйте позже.")
        logger.error("Не удалось получить медиа или клавиатуру для /start")
        return

    # Отправляем пользователю фото, используя данные, полученные из базы.
    await message.answer_photo(
        media.media, caption=media.caption, reply_markup=reply_markup
    )


# Обработчик команды /help.
@user_private_router.message(Command("help"))
async def help_cmd(message: types.Message) -> None:
    """
    Отправляет пользователю информацию о том, как пользоваться ботом-магазином.
    """
    help_text = (
        "🛍 **Добро пожаловать!**\n"
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
        "🎉 *Колпаки* – стильные аксессуары для вечеринок.\n\n"

        "📩 **Оформить заказ:**\n"
        "Нажмите «Оформить заказ» и напишите админу для уточнения деталей. 📞\n\n"

        "❓ Остались вопросы? Обращайтесь в поддержку! 💬"
    )

    await message.answer(help_text)


# Функция для добавления товара в корзину.
async def add_to_cart(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
) -> None:
    """
    Добавляет товар в корзину пользователя.

    1. Извлекает информацию о пользователе из callback.
    2. Регистрирует пользователя в базе, если его еще нет.
    3. Добавляет товар в корзину по product_id из callback_data.
    4. Отправляет уведомление об успешном добавлении товара.
    """
    # Получаем информацию о пользователе из callback.
    user_local = callback.from_user

    # Регистрируем пользователя в базе данных.
    await orm_add_user(
        session,
        user_id=user_local.id,
        first_name=user_local.first_name,
        last_name=user_local.last_name or "",
        phone=None,
    )
    # Добавляем выбранный товар в корзину.
    if callback_data.product_id is not None:
        await orm_add_to_cart(session, user_id=user_local.id,
                              product_id=callback_data.product_id)
        await callback.answer("Товар добавлен в корзину!")
        await session.commit()
    else:
        await callback.answer("Ошибка: отсутствует идентификатор товара.",
                              show_alert=True)


# Обработчик callback-запросов, формируемых через MenuCallBack.
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
        callback: types.CallbackQuery,
        callback_data: MenuCallBack,
        session: AsyncSession,
        notification_service: NotificationService = None,
) -> None:
    """
    Обрабатывает взаимодействие пользователя с меню.

    В зависимости от callback_data:
      - Если выбран "checkout" на уровне 4, оформляет заказ.
      - Если выбрано "add_to_cart", добавляет товар в корзину.
      - Для остальных действий обновляет контент меню.

    Аргументы:
      callback: объект CallbackQuery от Telegram.
      callback_data: данные callback, распарсенные через MenuCallBack.
      session: асинхронная сессия SQLAlchemy для работы с БД.
      notification_service: сервис уведомлений; если не передан,
       создается новый.
    """
    # Если сервис уведомлений не передан, инициализируем его.
    if notification_service is None:
        notification_service = NotificationService(
            bot=callback.bot,  # Получаем объект бота из callback.
            admin_chat_id=settings.ADMIN_CHAT_ID,
        )

    try:
        # Если выбран пункт "checkout" и уровень меню равен 4,
        # выполняем оформление заказа.
        if callback_data.menu_name == "checkout" and callback_data.level == 4:
            media, keyboards = await checkout(
                session, callback.from_user.id, notification_service
            )
            # Обновляем медиа-содержимое сообщения,
            # используя полученные данные.
            if (
                    callback.message
                    and isinstance(callback.message,
                                   types.Message)  # Проверка типа
                    and callback.message.photo  # Проверяем наличие медиа
            ):
                await callback.message.edit_media(
                    media=media,
                    reply_markup=keyboards
                )
            await callback.answer()
            return

        # Если выбрано действие "add_to_cart", добавляем товар в корзину.
        if callback_data.menu_name == "add_to_cart":
            await add_to_cart(callback, callback_data, session)
            return

        # Получаем контент меню из базы данных по данным,
        # переданным в callback.
        print(f"Передача параметров в get_menu_content: "
              f"level={callback_data.level}, menu_name={callback_data.menu_name}, "
              f"category={callback_data.category}, page={callback_data.page}, "
              f"user_id={callback.from_user.id}, product_id={callback_data.product_id}")

        logger.debug(f"Передача параметров в get_menu_content: "
                     f"level={callback_data.level}, menu_name={callback_data.menu_name}, "
                     f"category={callback_data.category}, page={callback_data.page}, "
                     f"user_id={callback.from_user.id}, product_id={callback_data.product_id}")

        media, reply_markup = await get_menu_content(
            session,
            level=callback_data.level,
            menu_name=callback_data.menu_name,
            category=callback_data.category,
            page=callback_data.page,
            user_id=callback.from_user.id,
            product_id=callback_data.product_id,
        )
        # Если медиа-контент не найден, уведомляем пользователя.
        if not media:
            await callback.answer("Медиа не найдено.", show_alert=True)
            return

        # Если media является строкой, оборачиваем ее в объект InputMediaPhoto.
        if isinstance(media, str):
            media = InputMediaPhoto(media=media)

        # Логгируем отладочную информацию о медиа и клавиатуре.
        logger.debug(f"Media: {media}")
        logger.debug(f"Reply Markup: {reply_markup}")

        # Проверяем доступность сообщения перед доступом к атрибутам
        if not callback.message or not isinstance(callback.message,
                                                  types.Message):
            await callback.answer("Сообщение недоступно!", show_alert=True)
            return

        # Получаем текущее медиа из сообщения
        current_media = (
            callback.message.photo[
                -1].file_id if callback.message and callback.message.photo else None
        )
        current_reply_markup = callback.message.reply_markup if callback.message else None

        # Проверяем, изменилось ли медиа или клавиатура
        is_media_changed = (
            current_media != media.media
            if isinstance(media, InputMediaPhoto)
            else True
        )
        is_markup_changed = current_reply_markup != reply_markup

        # Если медиа и клавиатура не изменились, не обновляем сообщение
        if not is_media_changed and not is_markup_changed:
            await callback.answer("Сообщение уже актуально.",
                                  show_alert=True)
            return

        # Пытаемся обновить сообщение пользователя с новым медиа и клавиатурой.
        try:
            # Дополнительная проверка перед редактированием
            if isinstance(callback.message, types.Message):
                await callback.message.edit_media(
                    media=media,
                    reply_markup=reply_markup)

        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.warning("Попытка изменить сообщение без изменений.")
            else:
                logger.error(f"Ошибка при изменении медиа: {e}",
                             exc_info=True)
                await callback.answer(
                    "Произошла ошибка при обновлении медиа.",
                    show_alert=True
                )
        finally:
            # Отправляем пустой ответ, чтобы закрыть ожидание Telegram.
            await callback.answer()
    except Exception as e:
        # Логгируем любую ошибку, возникшую в процессе обработки меню.
        logger.error(f"Ошибка в обработчике user_menu: {e}",
                     exc_info=True)
        await callback.answer(
            "Произошла ошибка при обработке запроса.",
            show_alert=True
        )
