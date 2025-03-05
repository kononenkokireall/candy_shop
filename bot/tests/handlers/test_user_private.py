from sqlite3 import DatabaseError
from unittest.mock import AsyncMock, patch, Mock

import pytest
from aiogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, OrderItem
from handlers.user_events.user_checkout import checkout, format_admin_notification
from handlers.user_events.user_main import user_menu
from keyboards.inline_main import MenuCallBack
from utilit.config import settings
from utilit.notification import NotificationService


@pytest.mark.asyncio
async def test_user_menu_checkout():
    # Мокируем зависимости
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=MenuCallBack, menu_name="checkout", level=4)
    session = AsyncMock(spec=AsyncSession)
    notification_service = AsyncMock(spec=NotificationService)

    # Мокируем checkout
    with patch("handlers.user_events.user_checkout", return_value=("media", "keyboards")) as mock_checkout:
        await user_menu(callback, callback_data, session, notification_service)

        # Проверяем вызов checkout
        mock_checkout.assert_awaited_once_with(session, callback.from_user.id, notification_service)

        # Проверяем обновление сообщения
        callback.message.edit_media.assert_awaited_once_with(media="media", reply_markup="keyboards")
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_menu_add_to_cart():
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=MenuCallBack, menu_name="add_to_cart")
    session = AsyncMock(spec=AsyncSession)

    with patch("your_module.add_to_cart") as mock_add:
        await user_menu(callback, callback_data, session)

        # Проверяем вызов add_to_cart
        mock_add.assert_awaited_once_with(callback, callback_data, session)
        callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_user_menu_general_case():
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(
        spec=MenuCallBack,
        menu_name="main",
        level=1,
        category="test_category",
        page=1,
        product_id=123
    )
    session = AsyncMock(spec=AsyncSession)

    # Мокируем get_menu_content для возврата строки как media
    with patch("your_module.get_menu_content", return_value=("test_media_str", "markup")):
        await user_menu(callback, callback_data, session)

        # Проверяем конвертацию media в InputMediaPhoto
        callback.message.edit_media.assert_awaited_once_with(
            media=InputMediaPhoto(media="test_media_str"),
            reply_markup="markup"
        )


@pytest.mark.asyncio
async def test_user_menu_error_handling():
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=MenuCallBack)
    session = AsyncMock(spec=AsyncSession)

    # Имитируем ошибку при edit_media
    callback.message.edit_media.side_effect = Exception("Test error")

    with patch("your_module.get_menu_content", return_value=("media", "markup")):
        await user_menu(callback, callback_data, session)

        # Проверяем логирование ошибки и ответ пользователю
        assert "Test error" in str(callback.message.edit_media.side_effect)
        callback.answer.assert_awaited_with("Произошла ошибка при обновлении медиа.", show_alert=True)


@pytest.mark.asyncio
async def test_notification_service_initialization():
    callback = AsyncMock(spec=CallbackQuery)
    callback_data = Mock(spec=MenuCallBack)
    session = AsyncMock(spec=AsyncSession)

    # Передаем notification_service как None
    with patch("your_module.NotificationService") as mock_service:
        await user_menu(callback, callback_data, session, notification_service=None)

        # Проверяем создание NotificationService
        mock_service.assert_called_once_with(
            bot=callback.bot,
            admin_chat_id=settings.ADMIN_CHAT_ID
        )




@pytest.mark.asyncio
async def test_checkout_success():
    """Успешное оформление заказа с непустой корзиной."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_notification = AsyncMock()

    # Мокируем данные корзины (2 товара)
    carts = [
        Mock(product=Mock(price=100), quantity=2, product_id=1),
        Mock(product=Mock(price=200), quantity=1, product_id=2),
    ]

    # Мокируем ORM-функции
    with patch("your_module.orm_get_banner", return_value=Mock()) as mock_banner, \
            patch("your_module.orm_get_user_carts", return_value=carts), \
            patch("your_module.orm_delete_from_cart") as mock_clear_cart, \
            patch("your_module.format_user_response",
                  return_value=(InputMediaPhoto(media="banner.jpg"), InlineKeyboardMarkup())):
        # Act
        result = await checkout(mock_session, user_id=1, notification_service=mock_notification)

        # Assert
        # Проверка создания заказа
        mock_session.add.assert_any_call(Order(
            user_id=1,
            total_price=2 * 100 + 1 * 200,  # 400
            status="pending"
        ))

        # Проверка добавления позиций заказа
        assert mock_session.add_all.call_count == 1
        added_items = mock_session.add_all.call_args[0][0]
        assert len(added_items) == 2
        assert isinstance(added_items[0], OrderItem)

        # Проверка очистки корзины
        mock_clear_cart.assert_awaited_once_with(mock_session, user_id=1)

        # Проверка уведомлений
        mock_notification.send_to_admin.assert_awaited()
        assert isinstance(result[0], InputMediaPhoto)


@pytest.mark.asyncio
async def test_checkout_empty_cart():
    """Попытка оформления с пустой корзиной."""
    with patch("your_module.orm_get_user_carts", return_value=[]), \
            pytest.raises(ValueError, match="Корзина пользователя пуста"):
        await checkout(AsyncMock(), user_id=1, notification_service=AsyncMock())


@pytest.mark.asyncio
async def test_checkout_database_error():
    """Ошибка при сохранении заказа в БД."""
    mock_session = AsyncMock()
    mock_session.commit.side_effect = DatabaseError("Test error")

    with patch("your_module.orm_get_user_carts", return_value=[Mock()]), \
            pytest.raises(DatabaseError):
        await checkout(mock_session, user_id=1, notification_service=AsyncMock())


@pytest.mark.asyncio
async def test_format_admin_notification_success():
    """Проверка форматирования уведомления для администратора."""
    # Мокируем заказ с пользователем и товарами
    mock_order = Mock(
        id=123,
        user=Mock(first_name="Test", phone="+123456789"),
        items=[
            Mock(product=Mock(name="Product1"), quantity=2, price=100),
            Mock(product=Mock(name="Product2"), quantity=1, price=200),
        ],
        total_price=400
    )

    with patch("your_module.session_maker", return_value=AsyncMock()), \
            patch("your_module.format_order_notification", return_value=("Admin Text", InlineKeyboardMarkup())):
        text, keyboard = await format_admin_notification(order_id=123)
        assert "Admin Text" in text
        assert isinstance(keyboard, InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_format_admin_notification_error():
    """Ошибка при запросе заказа."""
    with patch("your_module.session_maker", side_effect=Exception("DB Error")), \
            pytest.raises(Exception):
        await format_admin_notification(order_id=123)