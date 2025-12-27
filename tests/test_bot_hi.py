from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import hi


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
    message.text = "/hi"

    update = MagicMock()
    update.message = message

    return update


class TestHi:
    @patch("src.bot.handlers.hi.dc")
    @patch("src.bot.handlers.hi.util.is_admin_tg_user", return_value=True)
    @pytest.mark.anyio
    async def test_handle_with_admin_user(self, mock_is_admin, mock_dc, mock_update):
        """Test hi handler with admin user."""
        with patch("src.bot.handlers.hi.random_reply", return_value="hi"):
            await hi.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("hi", mock_update)
            mock_update.message.reply_text.assert_called_once_with("hi")

    @patch("src.bot.handlers.hi.dc")
    @patch("src.bot.handlers.hi.util")
    @pytest.mark.anyio
    async def test_handle_with_non_admin_user(self, mock_util, mock_dc, mock_update):
        """Test hi handler with non-admin user."""
        mock_util.is_admin_tg_user.return_value = False

        await hi.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_not_called()
        mock_update.message.reply_text.assert_not_called()

    @patch("src.bot.handlers.hi.dc")
    @patch("src.bot.handlers.hi.util.is_admin_tg_user", return_value=True)
    @pytest.mark.anyio
    async def test_handle_without_logging(self, mock_is_admin, mock_dc, mock_update):
        """Test hi handler with log_to_dc=False."""
        with patch("src.bot.handlers.hi.random_reply", return_value="bc"):
            await hi.handle(mock_update, MagicMock(), log_to_dc=False)

            mock_dc.log_command_usage.assert_not_called()
            mock_update.message.reply_text.assert_called_once_with("bc")

    def test_random_reply(self):
        """Test random reply generation."""
        result = hi.random_reply()

        assert result in ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]
