from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import quotes
from src.db import Bakchod


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
    message.text = "/quotes"
    message.reply_to_message = None

    reply_message = MagicMock(spec=Message)
    reply_message.text = "This is a quote"
    reply_message.from_user = user

    update = MagicMock()
    update.message = message
    update.message.reply_to_message = reply_message

    return update


@pytest.fixture
def mock_quote():
    """Create a mock Quote object."""
    quote = MagicMock()
    quote.quote_id = 1
    quote.text = "This is a quote"
    quote.created = "2024-01-01 12:00:00"

    mock_author = MagicMock(spec=Bakchod)
    mock_author.username = "testuser"
    mock_author.first_name = "Test"
    quote.author_bakchod = mock_author

    return quote


class TestQuotes:
    @patch("src.bot.handlers.quotes.util")
    @patch("src.bot.handlers.quotes.quote_dao")
    @patch("src.bot.handlers.quotes.dc")
    @pytest.mark.anyio
    async def test_handle_random_quote(self, mock_dc, mock_quote_dao, mock_util, mock_update):
        """Test quotes handler with random quote."""
        mock_util.get_group_id_from_update.return_value = "-1001234567890"

        mock_quote = MagicMock()
        mock_quote.quote_id = 1
        mock_quote.text = "Test quote"
        mock_quote.author_bakchod = MagicMock()
        mock_quote.author_bakchod.username = "testuser"
        mock_quote.author_bakchod.first_name = "Test"
        mock_quote.created = "2024-01-01"

        mock_quote_dao.add_quote.side_effect = Exception("Not adding")
        mock_util.extract_pretty_name_from_bakchod.return_value = "@testuser"

        with patch("src.bot.handlers.quotes.get_random_quote_from_group", return_value=mock_quote):
            await quotes.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("quotes", mock_update)

    @patch("src.bot.handlers.quotes.util")
    @patch("src.bot.handlers.quotes.dc")
    @pytest.mark.anyio
    async def test_handle_get_quote_missing_id(self, mock_dc, mock_util, mock_update):
        """Test quotes handler get command without ID."""
        mock_update.message.text = "/quotes get"

        await quotes.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("quotes", mock_update)
        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.quotes.util")
    @patch("src.bot.handlers.quotes.dc")
    @pytest.mark.anyio
    async def test_handle_remove_quote_admin(self, mock_dc, mock_util, mock_update):
        """Test quotes handler remove command by admin."""
        mock_update.message.text = "/quotes remove 1"
        mock_util.is_admin_tg_user.return_value = True

        with patch("src.bot.handlers.quotes.Quote") as mock_quote:
            mock_quote.delete_by_id.return_value = 1

            await quotes.handle(mock_update, MagicMock())

            mock_dc.log_command_usage.assert_called_once_with("quotes", mock_update)
            mock_quote.delete_by_id.assert_called_once_with("1")

    @patch("src.bot.handlers.quotes.util")
    @patch("src.bot.handlers.quotes.dc")
    @pytest.mark.anyio
    async def test_handle_remove_quote_non_admin(self, mock_dc, mock_util, mock_update):
        """Test quotes handler remove command by non-admin."""
        mock_update.message.text = "/quotes remove 1"
        mock_util.is_admin_tg_user.return_value = False

        await quotes.handle(mock_update, MagicMock())

        mock_dc.log_command_usage.assert_called_once_with("quotes", mock_update)
        mock_update.message.reply_text.assert_called_once()

    def test_generate_pretty_quote(self):
        """Test generate_pretty_quote function."""
        mock_quote = MagicMock()
        mock_quote.quote_id = 1
        mock_quote.text = "Test quote"
        mock_quote.created = "2024-01-01"
        mock_quote.author_bakchod = MagicMock()
        mock_quote.author_bakchod.username = "testuser"

        with patch(
            "src.bot.handlers.quotes.util.extract_pretty_name_from_bakchod",
            return_value="@testuser",
        ):
            result = quotes.generate_pretty_quote(mock_quote)

            assert "Test quote" in result
            assert "@testuser" in result
            assert "2024-01-01" in result
            assert "1" in result

    @patch("src.bot.handlers.quotes.Quote")
    def test_get_random_quote_from_group(self, mock_quote):
        """Test get_random_quote_from_group function."""
        mock_quote_obj = MagicMock()
        mock_quote_obj.quote_id = 1
        mock_quote_obj.text = "Test quote"

        mock_query = MagicMock()
        mock_query.execute.return_value = [mock_quote_obj]
        mock_quote.select.return_value.where.return_value = mock_query

        result = quotes.get_random_quote_from_group("-1001234567890")

        assert result is not None

    @patch("src.bot.handlers.quotes.Quote")
    def test_get_random_quote_from_group_empty(self, mock_quote):
        """Test get_random_quote_from_group with no quotes."""
        mock_query = MagicMock()
        mock_query.execute.return_value = []
        mock_quote.select.return_value.where.return_value = mock_query

        result = quotes.get_random_quote_from_group("-1001234567890")

        assert result is None
