from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import translate


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
    message.text = "/translate"
    message.reply_to_message = None

    reply_message = MagicMock(spec=Message)
    reply_message.text = "Hello world"
    reply_message.caption = None

    update = MagicMock()
    update.message = message
    update.message.reply_to_message = reply_message

    return update


class TestTranslate:
    @patch("src.bot.handlers.translate.translator")
    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_success(self, mock_dc, mock_translator, mock_update):
        """Test translate handler success case."""
        mock_translation = MagicMock()
        mock_translation.text = "Hola mundo"
        mock_translation.src = "en"
        mock_translation.dest = "es"
        mock_translator.translate.return_value = mock_translation

        await translate.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
        mock_translator.translate.assert_called_once_with(text="Hello world", dest="en")
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_no_reply(self, mock_dc, mock_update):
        """Test translate handler without reply."""
        mock_update.message.reply_to_message = None

        await translate.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_with_target_language(self, mock_dc, mock_update):
        """Test translate handler with target language specified."""
        mock_update.message.text = "/translate es"
        mock_translator = MagicMock()
        mock_translation = MagicMock()
        mock_translation.text = "Hola mundo"
        mock_translation.src = "en"
        mock_translation.dest = "es"
        mock_translator.translate.return_value = mock_translation

        with patch("src.bot.handlers.translate.translator", mock_translator):
            await translate.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
            mock_translator.translate.assert_called_once_with(text="Hello world", dest="es")

    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_no_text_to_translate(self, mock_dc, mock_update):
        """Test translate handler when no text is found."""
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = None

        await translate.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.translate.translator")
    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_with_caption(self, mock_dc, mock_translator, mock_update):
        """Test translate handler with caption instead of text."""
        mock_update.message.reply_to_message.text = None
        mock_update.message.reply_to_message.caption = "Caption text"

        mock_translation = MagicMock()
        mock_translation.text = "Texto de leyenda"
        mock_translation.src = "en"
        mock_translation.dest = "es"
        mock_translator.translate.return_value = mock_translation

        await translate.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
        mock_translator.translate.assert_called_once_with(text="Caption text", dest="en")

    @patch("src.bot.handlers.translate.translator")
    @patch("src.bot.handlers.translate.dc")
    @pytest.mark.anyio
    async def test_handle_with_exception(self, mock_dc, mock_translator, mock_update):
        """Test translate handler when translation fails."""
        mock_translator.translate.side_effect = Exception("Translation error")

        await translate.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("translate", mock_update)
        mock_update.message.reply_text.assert_called_once()
