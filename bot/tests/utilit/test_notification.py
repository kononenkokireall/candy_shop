from unittest.mock import Mock, AsyncMock

import pytest
from aiogram import Bot

from utilit.notification import NotificationService


@pytest.mark.asyncio
async def test_send_to_admin_success():
    """Успешная отправка сообщения администратору"""
    # Arrange
    mock_bot = AsyncMock(spec=Bot)
    admin_chat_id = 123
    notification_service = NotificationService(mock_bot, admin_chat_id)
    text = "Test message"
    kwargs = {"parse_mode": "HTML"}

    # Act
    await notification_service.send_to_admin(text, **kwargs)

    # Assert
    mock_bot.send_message.assert_awaited_once_with(
        chat_id=admin_chat_id,
        text=text,
        **kwargs
    )

@pytest.mark.asyncio
async def test_send_to_admin_error_propagation():
    """Проверка проброса исключения из bot.send_message"""
    # Arrange
    mock_bot = AsyncMock(spec=Bot)
    mock_bot.send_message.side_effect = Exception("API Error")
    notification_service = NotificationService(mock_bot, 123)

    # Act & Assert
    with pytest.raises(Exception, match="API Error"):
        await notification_service.send_to_admin("Test")

@pytest.mark.asyncio
async def test_send_to_admin_with_additional_args():
    """Проверка передачи дополнительных аргументов"""
    # Arrange
    mock_bot = AsyncMock(spec=Bot)
    notification_service = NotificationService(mock_bot, 123)
    kwargs = {
        "parse_mode": "Markdown",
        "reply_markup": Mock(),
        "disable_notification": True
    }

    # Act
    await notification_service.send_to_admin("Test", **kwargs)

    # Assert
    mock_bot.send_message.assert_awaited_once_with(
        chat_id=123,
        text="Test",
        **kwargs
    )