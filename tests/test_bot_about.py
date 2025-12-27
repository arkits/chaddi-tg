from unittest.mock import MagicMock, patch

import pytest
from telegram import Chat, Message, User

from src.bot.handlers import about


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
    message.text = "/about"
    message.reply_to_message = None

    update = MagicMock()
    update.message = message

    return update


class TestAbout:
    @patch("src.bot.handlers.about.dc")
    @patch("src.bot.handlers.about.bakchod_dao")
    @pytest.mark.anyio
    async def test_handle_with_reply_to_message(self, mock_bakchod_dao, mock_dc, mock_update):
        """Test about handler when replying to a message."""
        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 123456
        mock_bakchod.rokda = 100.0
        mock_bakchod.lastseen = "2024-01-01 12:00:00"
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        await about.handle(mock_update, MagicMock())

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.assert_called_once()

    @patch("src.bot.handlers.about.dc")
    @patch("src.bot.handlers.about.bakchod_dao")
    @pytest.mark.anyio
    async def test_handle_without_username(self, mock_bakchod_dao, mock_dc, mock_update):
        """Test about handler without username parameter."""
        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 123456
        mock_bakchod.rokda = 100.0
        mock_bakchod.lastseen = "2024-01-01 12:00:00"
        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        await about.handle(mock_update, MagicMock())

        mock_update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.about.dc")
    @patch("src.bot.handlers.about.bakchod_dao")
    @pytest.mark.anyio
    async def test_handle_with_username_not_found(self, mock_bakchod_dao, mock_dc):
        """Test about handler with username that doesn't exist."""
        user = MagicMock()
        user.id = 123456

        chat = MagicMock()
        chat.id = -1001234567890

        message = MagicMock()
        message.message_id = 1
        message.from_user = user
        message.chat = chat
        message.text = "/about nonexistent"
        message.reply_to_message = None

        update = MagicMock()
        update.message = message

        mock_bakchod_dao.get_bakchod_by_username.return_value = None

        await about.handle(update, MagicMock())

        assert "Kaun hai bee 'nonexistent'" in message.reply_text.call_args[0][0]

    @patch("src.bot.handlers.about.dc")
    @patch("src.bot.handlers.about.bakchod_dao")
    @pytest.mark.anyio
    async def test_handle_with_username(self, mock_bakchod_dao, mock_dc):
        """Test about handler with username parameter."""
        user = MagicMock()
        user.id = 123456

        chat = MagicMock()
        chat.id = -1001234567890

        message = MagicMock()
        message.message_id = 1
        message.from_user = user
        message.chat = chat
        message.text = "/about @testuser"
        message.reply_to_message = None

        update = MagicMock()
        update.message = message

        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 123456
        mock_bakchod.rokda = 100.0
        mock_bakchod.lastseen = "2024-01-01 12:00:00"
        mock_bakchod_dao.get_bakchod_by_username.return_value = mock_bakchod

        await about.handle(update, MagicMock())

        update.message.reply_text.assert_called_once()

    @patch("src.bot.handlers.about.dc")
    @pytest.mark.anyio
    async def test_handle_exception(self, mock_dc):
        """Test about handler exception handling."""
        user = MagicMock()
        user.id = 123456

        chat = MagicMock()
        chat.id = -1001234567890

        message = MagicMock()
        message.message_id = 1
        message.from_user = user
        message.chat = chat
        message.text = "/about"
        message.reply_to_message = None

        update = MagicMock()
        update.message = message

        with patch(
            "src.bot.handlers.about.bakchod_dao.get_or_create_bakchod_from_tg_user",
            side_effect=Exception("Test error"),
        ):
            await about.handle(update, MagicMock())

    def test_parse_username_with_at_symbol(self):
        """Test parsing username with @ symbol."""
        result = about.parse_username("/about @testuser")

        assert result == "testuser"

    def test_parse_username_without_at_symbol(self):
        """Test parsing username without @ symbol."""
        result = about.parse_username("/about testuser")

        assert result == "testuser"

    def test_parse_username_no_argument(self):
        """Test parsing username when no argument provided."""
        result = about.parse_username("/about")

        assert result is None

    def test_generate_about_response(self):
        """Test generating about response."""
        mock_bakchod = MagicMock()
        mock_bakchod.tg_id = 123456
        mock_bakchod.rokda = 100.0
        mock_bakchod.lastseen = "2024-01-01 12:00:00"

        with patch(
            "src.bot.handlers.about.util.extract_pretty_name_from_bakchod", return_value="@testuser"
        ):
            result = about.generate_about_response(mock_bakchod)

            assert "@testuser" in result
            assert "123456" in result
            assert "100.0" in result
            assert "2024-01-01 12:00:00" in result
