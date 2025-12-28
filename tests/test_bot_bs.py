from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import bs


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
    message.text = "/bs"

    update = MagicMock()
    update.message = message

    return update


class TestBs:
    @patch("src.bot.handlers.bs.dc")
    @pytest.mark.anyio
    async def test_handle(self, mock_dc, mock_update):
        """Test bs handler generates bullshit."""
        with patch("src.bot.handlers.bs.generate_bullshit", return_value="Test bullshit."):
            await bs.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("bs", mock_update)
            mock_update.message.reply_text.assert_called_once_with("Test bullshit.")

    def test_generate_bullshit(self):
        """Test bullshit generation produces valid output."""
        result = bs.generate_bullshit()

        assert isinstance(result, str)
        assert len(result) > 0
        assert result[0].isupper()
        assert result.endswith(".")

    def test_sentence_structure(self):
        """Test sentence structure is correct."""
        result = bs.generate_bullshit()

        assert result.endswith(".")
        assert result[0].isupper()
