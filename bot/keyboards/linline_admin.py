# Импортируем необходимые классы для работы
# с callback-данными и inline-клавиатурами
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем callback-класс для главного меню
from keyboards.inline_main import MenuCallBack

# Импортируем настройки (например, ADMIN_CHAT_ID) из конфигурационного файла
from utilit.config import settings


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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    # Формируем callback-данные
                    # для подтверждения заказа с указанным order_id
                    callback_data=OrderAction(
                        action="confirm", order_id=order_id
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    # Формируем callback-данные
                    # для отмены заказа с указанным order_id
                    callback_data=OrderAction(
                        action="cancel", order_id=order_id
                    ).pack(),
                ),
            ]
        ]
    )


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
    keyboard.add(
        InlineKeyboardButton(
            text="Чат с админом 💬",
            url=f"tg://user?id={settings.ADMIN_CHAT_ID}"
        ),
        InlineKeyboardButton(
            text="🏠Обратно в меню",
            callback_data=MenuCallBack(level=0, menu_name="main").pack(),
        ),
    )

    # Организуем кнопки в ряды (по одной кнопке в ряду)
    keyboard.adjust(1)

    # Преобразуем билдера в итоговую разметку клавиатуры и возвращаем её
    return keyboard.as_markup()
