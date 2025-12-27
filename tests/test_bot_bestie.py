from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import bestie


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 222021705
    user.username = "bestie1"
    user.first_name = "Bestie"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/bestie"

    update = MagicMock()
    update.message = message

    return update


class TestBestie:
    @patch("src.bot.handlers.bestie.dc")
    @pytest.mark.anyio
    async def test_handle_with_bestie_user(self, mock_dc, mock_update):
        """Test bestie handler with bestie user."""
        mock_update.message.from_user.id = 222021705

        with patch("src.bot.handlers.bestie.random_reply", return_value="gussa aa ri"):
            await bestie.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("bestie", mock_update)
            mock_update.message.reply_text.assert_called_once_with("gussa aa ri")

    @patch("src.bot.handlers.bestie.dc")
    @pytest.mark.anyio
    async def test_handle_with_second_bestie_user(self, mock_dc, mock_update):
        """Test bestie handler with second bestie user."""
        mock_update.message.from_user.id = 148933790

        with patch("src.bot.handlers.bestie.random_reply", return_value="nhi ho ra"):
            await bestie.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("bestie", mock_update)
            mock_update.message.reply_text.assert_called_once_with("nhi ho ra")

    @patch("src.bot.handlers.bestie.dc")
    @pytest.mark.anyio
    async def test_handle_with_non_bestie_user(self, mock_dc, mock_update):
        """Test bestie handler with non-bestie user."""
        mock_update.message.from_user.id = 999999

        await bestie.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_not_called()
        mock_update.message.reply_text.assert_not_called()

    @patch("src.bot.handlers.bestie.dc")
    @pytest.mark.anyio
    async def test_handle_without_logging(self, mock_dc, mock_update):
        """Test bestie handler with log_to_dc=False."""
        mock_update.message.from_user.id = 222021705

        with patch("src.bot.handlers.bestie.random_reply", return_value="chid chid ho ra"):
            await bestie.handle(mock_update, MagicMock(), log_to_dc=False)

            mock_dc.log_command_usage.assert_not_called()
            mock_update.message.reply_text.assert_called_once_with("chid chid ho ra")

    @patch("src.bot.handlers.bestie.random")
    def test_random_reply(self, mock_random):
        """Test random_reply function."""
        mock_random.randint.return_value = 2

        result = bestie.random_reply()

        mock_random.randint.assert_called_once_with(0, 5)
        assert result == "chid chid ho ra"
