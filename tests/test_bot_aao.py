from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import aao


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    user = MagicMock(spec=User)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"

    reply_user = MagicMock(spec=User)
    reply_user.id = 789012
    reply_user.username = "replyuser"
    reply_user.first_name = "Reply"

    chat = MagicMock(spec=Chat)
    chat.id = -1001234567890
    chat.type = "group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/aao"
    message.reply_to_message = None

    reply_message = MagicMock(spec=Message)
    reply_message.from_user = reply_user
    reply_message.text = "Hello there"

    update = MagicMock()
    update.message = message
    update.message.reply_to_message = reply_message

    return update


class TestAao:
    @patch("src.bot.handlers.aao.dc")
    @patch("src.bot.handlers.aao.util")
    @patch("src.bot.handlers.aao.mom_spacy")
    @pytest.mark.anyio
    async def test_handle_success(self, mock_mom_spacy, mock_util, mock_dc, mock_update):
        """Test aao handler success case."""
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Hello there"
        mock_util.extract_magic_word.return_value = "hello"

        await aao.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("aao", mock_update)
        mock_util.paywall_user.assert_called_once()
        mock_mom_spacy.extract_target_message.assert_called_once()
        mock_util.extract_magic_word.assert_called_once_with("Hello there")

    @patch("src.bot.handlers.aao.dc")
    @patch("src.bot.handlers.aao.util")
    @pytest.mark.anyio
    async def test_handle_no_rokda(self, mock_util, mock_dc, mock_update):
        """Test aao handler without enough rokda."""
        mock_util.paywall_user.return_value = False

        await aao.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("aao", mock_update)
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.aao.dc")
    @patch("src.bot.handlers.aao.util")
    @patch("src.bot.handlers.aao.mom_spacy")
    @pytest.mark.anyio
    async def test_handle_no_target_message(self, mock_mom_spacy, mock_util, mock_dc, mock_update):
        """Test aao handler when no target message is extracted."""
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = None

        await aao.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("aao", mock_update)
        mock_update.message.reply_text.assert_not_called()

    @patch("src.bot.handlers.aao.dc")
    @patch("src.bot.handlers.aao.util")
    @patch("src.bot.handlers.aao.mom_spacy")
    @pytest.mark.anyio
    async def test_handle_no_magic_word(self, mock_mom_spacy, mock_util, mock_dc, mock_update):
        """Test aao handler when no magic word is found."""
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Hello there"
        mock_util.extract_magic_word.return_value = None

        await aao.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("aao", mock_update)
        mock_update.message.reply_text.assert_not_called()

    @patch("src.bot.handlers.aao.dc")
    @patch("src.bot.handlers.aao.util")
    @patch("src.bot.handlers.aao.mom_spacy")
    @pytest.mark.anyio
    async def test_handle_with_reply(self, mock_mom_spacy, mock_util, mock_dc, mock_update):
        """Test aao handler when replying to a message."""
        mock_util.paywall_user.return_value = True
        mock_mom_spacy.extract_target_message.return_value = "Hello there"
        mock_util.extract_magic_word.return_value = "hello"

        await aao.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("aao", mock_update)
        mock_update.message.reply_to_message.reply_text.assert_called_once()

    @patch("src.bot.handlers.aao.util")
    def test_get_support_word(self, mock_util):
        """Test get_support_word function."""
        mock_util.choose_random_element_from_list.return_value = "dikhae"

        result = aao.get_support_word()

        assert result == "dikhae"
        mock_util.choose_random_element_from_list.assert_called_once_with(
            ["dikhae", "sikhae", "kare"]
        )
