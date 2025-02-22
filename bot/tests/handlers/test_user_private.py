from unittest.mock import MagicMock, ANY

from aiogram.fsm.context import FSMContext

from handlers.user_events.user_main import start_cmd


async def test_start_handler(bot, dispatcher):
    message = MagicMock(text="/start")
    await start_cmd(message, MagicMock(spec=FSMContext))

    bot.send_message.assert_called_with(
        chat_id=message.chat.id,
        text="Добро пожаловать!",
        reply_markup=ANY
    )