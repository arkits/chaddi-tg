from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import superpower


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/superpower"

    update = MagicMock()
    update.message = message

    return update


class TestSuperpower:
    @patch("src.bot.handlers.superpower.dc")
    @pytest.mark.anyio
    async def test_handle(self, mock_dc, mock_update):
        """Test superpower handler."""
        with patch("src.bot.handlers.superpower.superpower_countdown_calc") as mock_calc:
            mock_calc.return_value = "Test Response"

            await superpower.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("superpower", mock_update)
            mock_calc.assert_called_once()
            mock_update.message.reply_text.assert_called_once_with("Test Response")

    @patch("src.bot.handlers.superpower.dc")
    @pytest.mark.anyio
    async def test_handle_with_exception(self, mock_dc, mock_update):
        """Test superpower handler when an exception occurs."""
        with patch("src.bot.handlers.superpower.superpower_countdown_calc") as mock_calc:
            mock_calc.side_effect = Exception("Error")

            await superpower.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("superpower", mock_update)

    @patch("src.bot.handlers.superpower.util")
    def test_superpower_countdown_calc_future(self, mock_util):
        """Test superpower_countdown_calc when superpower day is in future."""
        with patch("src.bot.handlers.superpower.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2019, 6, 1, 0, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            mock_util.pretty_time_delta.return_value = "7 months"

            result = superpower.superpower_countdown_calc()

            assert "Time Until Super Power" in result
            assert "7 months" in result
            mock_util.pretty_time_delta.assert_called_once()

    @patch("src.bot.handlers.superpower.util")
    def test_superpower_countdown_calc_past(self, mock_util):
        """Test superpower_countdown_calc when superpower day is in past."""
        with patch("src.bot.handlers.superpower.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 6, 1, 0, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            mock_util.pretty_time_delta.return_value = "5 months"

            result = superpower.superpower_countdown_calc()

            assert "WE INVANT SUPER POWER" in result
            assert "Time Since" in result
            assert "5 months" in result
            mock_util.pretty_time_delta.assert_called_once()
