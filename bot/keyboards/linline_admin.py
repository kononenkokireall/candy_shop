# Импортируем необходимые классы для работы
# с callback-данными и inline-клавиатурами
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем callback-класс для главного меню
from keyboards.inline_main import MenuCallBack

# Импортируем настройки (например, ADMIN_CHAT_ID) из конфигурационного файла
from utilit.config import settings

__all__ = [
    "OrderAction",
    "build_admin_keyboard",
    "build_user_keyboard",
]


# Класс OrderAction используется для формирования callback-данных для заказа.
# Он наследует CallbackData и автоматически добавляет префикс "order"
# к callback-данным.
class OrderAction(CallbackData, prefix="order"):
    action: str  # Действие, например, confirm (подтвердить),
    # cancel (отменить) или details (подробности)
    order_id: int  # Идентификатор заказа, к которому относится действие


# Функция build_admin_keyboard создает inline-клавиатуру для администратора,
# позволяющую подтверждать или отменять заказ по его идентификатору.
def build_admin_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    «✅ Подтвердить / ❌ Отменить» – для админа под карточкой заказа.
    """
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=OrderAction(action="confirm",
                                      order_id=order_id).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=OrderAction(action="cancel",
                                      order_id=order_id).pack(),
        ),
    )

    return keyboard.as_markup()


# Функция build_user_keyboard создает inline-клавиатуру для пользователя.
def build_user_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для пользователя с кнопками:
      - "Чат с админом": кнопка открывает чат с администратором.
      - "Обратно в меню": кнопка возвращает пользователя в главное меню.
    """
    # Создаем билдер для формирования inline-клавиатуры
    keyboard = InlineKeyboardBuilder()

    # Добавляем две кнопки в клавиатуру:
    # Первая кнопка: открывает чат с администратором по URL,
    # который формируется с использованием ADMIN_CHAT_ID
    # Вторая кнопка: возвращает пользователя в главное меню,
    # передавая соответствующие callback-данные
    admin_chat_id = getattr(settings, "ADMIN_CHAT_ID", None)
    if not admin_chat_id:
        # оставить только кнопку «Обратно в меню»,
        # если ID администратора не задан в конфиге
        keyboard.add(
            InlineKeyboardButton(
                text="🏠 Обратно в меню",
                callback_data=MenuCallBack(level=0,
                                           menu_name="main").pack(),
            )
        )
        return keyboard.as_markup()

    keyboard.row(  # каждая кнопка в своём ряду
        InlineKeyboardButton(
            text="Чат с админом 💬",
            url=f"tg://user?id={admin_chat_id}",
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="🏠 Обратно в меню",
            callback_data=MenuCallBack(level=0,
                                       menu_name="main").pack(),
        )
    )

    return keyboard.as_markup()
