import logging
from typing import Optional

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, Product, OrderStatus
from database.orm_querys.orm_query_banner import (
    orm_get_info_pages,
    orm_change_banner_image,

)
from database.orm_querys.orm_query_category import orm_get_categories
from database.orm_querys.orm_query_product import (
    orm_get_product,
    orm_get_products,
    orm_update_product,
    orm_add_product,
    orm_delete_product
)

from filters.chat_types import ChatTypeFilter, IsAdmin

from keyboards.inline_main import get_callback_btn
from keyboards.linline_admin import OrderAction

from keyboards.reply import get_keyboard

from states.states import OrderProcess, AddBanner

# Создаем роутер для работы с администраторами

admin_router_root = Router(name="admin_root")
# Устанавливаем фильтр для работы только
# в личных сообщениях и только для администраторов
admin_router_root.message.filter(ChatTypeFilter(["private"]), IsAdmin())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Handler для удаления товара
@admin_router_root.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(
        callback: types.CallbackQuery,
        session: AsyncSession
) -> None:
    # Получаем ID продукта для удаления
    """Обработчик удаления товара с проверкой данных"""
    # Проверяем наличие callback.data
    if not callback.data:
        await callback.answer("❌ Ошибка: отсутствуют данные",
                              show_alert=True)
        return

    # Безопасное разделение данных
    parts = callback.data.split("_")
    if len(parts) < 2 or not parts[-1].isdigit():
        await callback.answer("⚠️ Неверный формат запроса",
                              show_alert=True)
        return

    product_id = int(parts[-1])

    try:
        # Удаление товара
        await orm_delete_product(session, product_id)
        await callback.answer("✅ Товар удален")

        # Отправка подтверждения с проверкой сообщения
        if callback.message and isinstance(callback.message, types.Message):
            await callback.message.answer("🗑️ Товар успешно удален!")
        else:
            logger.warning("Сообщение недоступно для ответа")

    except Exception as e:
        logger.error(f"Ошибка удаления товара: {str(e)}")
        await callback.answer("🚨 Ошибка при удалении", show_alert=True)


# Обработчик callback-запроса для подтверждения заказа.
@admin_router_root.callback_query(OrderAction.filter(F.action == "confirm"))
async def confirm_order_handler(
        callback: types.CallbackQuery,
        callback_data: OrderAction,
        session: AsyncSession,
) -> None:
    if callback.message is None:
        logger.error("Callback без message")
        return

    order_id = callback_data.order_id

    try:
        # --- 1. блокируем строку заказа -----------------------------------
        order: Order | None = await session.get(
            Order, order_id, with_for_update=True
        )
        if not order:
            await callback.answer("🚨 Заказ не найден", show_alert=True)
            return

        if order.status == OrderStatus.CONFIRMED:
            await callback.answer("ℹ️ Уже подтверждён")
            return

        # --- 2. меняем статус и сохраняем ---------------------------------
        order.status = OrderStatus.CONFIRMED
        await session.commit()  # ← коммит тут

        # --- 3. уведомляем покупателя -------------------------------------
        try:
            await callback.bot.send_message(
                order.user_id,
                "<b>🎉 Ваш заказ подтверждён!</b>\n\n"
                "✅ Оплата получена\n"
                "📦 Получить можно по адресу: ул. Примерная 123",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Не смог отправить клиенту: %s", e)

        await callback.answer("✅ Заказ подтверждён")

    except SQLAlchemyError as db_err:
        await session.rollback()  # ← rollback ТОЛЬКО здесь
        logger.error("DB-ошибка подтверждения: %s", db_err, exc_info=True)
        await callback.answer("🚨 Ошибка БД", show_alert=True)

    except Exception as e:
        await session.rollback()
        logger.error("Ошибка подтверждения: %s", e, exc_info=True)
        await callback.answer("🚨 Ошибка подтверждения", show_alert=True)


@admin_router_root.callback_query(OrderAction.filter(F.action == "cancel"))
async def cancel_order_handler(
        callback: types.CallbackQuery,
        callback_data: OrderAction,
        session: AsyncSession,
) -> None:
    """
    ❌ Обработчик «Отменить заказ».
    """
    # --- базовые проверки --------------------------------------------------
    if callback.message is None:
        logger.error("Callback без message")
        return

    if not callback.bot:
        logger.error("Bot instance отсутствует")
        await callback.answer("❌ Ошибка системы", show_alert=True)
        return

    order_id = callback_data.order_id

    try:
        # --- 1. блокируем строку заказа ------------------------------------
        order: Order | None = await session.get(
            Order, order_id, with_for_update=True
        )
        if not order:
            await callback.answer("🚨 Заказ не найден", show_alert=True)
            return

        if order.status == OrderStatus.CANCELLED:
            await callback.answer("ℹ️ Уже отменён")
            return

        # --- 2. ставим статус CANCELLED и сохраняем ------------------------
        order.status = OrderStatus.CANCELLED
        await session.commit()

        # --- 3. уведомляем покупателя -------------------------------------
        try:
            await callback.bot.send_message(
                order.user_id,
                "<b>❌ Заказ отменён.</b>\n\n"
                "Если нужны детали – свяжитесь с администратором.",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Не смог уведомить клиента: %s", e)

        await callback.answer("❌ Заказ отменён")

    except SQLAlchemyError as db_err:
        await session.rollback()
        logger.error("DB-ошибка отмены: %s", db_err, exc_info=True)
        await callback.answer("🚨 Ошибка БД", show_alert=True)

    except Exception as e:
        await session.rollback()
        logger.error("Ошибка отмены: %s", e, exc_info=True)
        await callback.answer("🚨 Ошибка отмены заказа", show_alert=True)
