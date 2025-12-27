from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import help as help_handler
from src.bot.handlers import ping, rokda, start


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
    chat.title = "Test Group"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "/ping"
    message.reply_to_message = None
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


def test_ping_random_reply():
    """Test that ping handler returns a random reply from the list."""
    reply = ping.random_reply()

    assert reply in ["pong", "ping", "pong bsdk", "ping bsdk", "bhaak sale"]


def test_ping_handle_with_admin_user(mock_update, mock_context):
    """Test ping handler with admin user."""
    with (
        patch("src.bot.handlers.ping.dc") as _mock_dc,
        patch("src.bot.handlers.ping.util") as mock_util,
    ):
        mock_util.is_admin_tg_user.return_value = True

        import asyncio

        asyncio.run(ping.handle(mock_update, mock_context))

        assert mock_update.message.reply_text.called


def test_ping_handle_with_non_admin_user(mock_update, mock_context):
    """Test ping handler with non-admin user."""
    with (
        patch("src.bot.handlers.ping.dc") as _mock_dc,
        patch("src.bot.handlers.ping.util") as mock_util,
    ):
        mock_util.is_admin_tg_user.return_value = False

        import asyncio

        asyncio.run(ping.handle(mock_update, mock_context))

        assert not mock_update.message.reply_text.called


def test_start_handle(mock_update, mock_context):
    """Test start handler."""
    with patch("src.bot.handlers.start.dc") as _mock_dc:
        import asyncio

        asyncio.run(start.handle(mock_update, mock_context))

        mock_update.message.reply_text.assert_called_once_with("Hi!")


def test_help_handle(mock_update, mock_context):
    """Test help handler."""
    with patch("src.bot.handlers.help.dc") as _mock_dc:
        import asyncio

        asyncio.run(help_handler.handle(mock_update, mock_context))

        assert mock_update.message.reply_text.called


def test_rokda_handle(mock_update, mock_context):
    """Test rokda handler without reply_to_message."""
    with (
        patch("src.bot.handlers.rokda.dc") as _mock_dc,
        patch("src.bot.handlers.rokda.bakchod_dao") as mock_bakchod_dao,
    ):
        mock_bakchod = MagicMock()
        mock_bakchod.username = "testuser"
        mock_bakchod.pretty_name = "Test User"
        mock_bakchod.rokda = 100.5

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        import asyncio

        asyncio.run(rokda.handle(mock_update, mock_context))

        assert mock_update.message.reply_text.called


def test_rokda_handle_with_reply(mock_update, mock_context):
    """Test rokda handler with reply_to_message."""
    with (
        patch("src.bot.handlers.rokda.dc") as _mock_dc,
        patch("src.bot.handlers.rokda.bakchod_dao") as mock_bakchod_dao,
    ):
        reply_user = MagicMock(spec=User)
        reply_user.id = 789012
        reply_user.username = "replyuser"

        mock_update.message.reply_to_message = MagicMock()
        mock_update.message.reply_to_message.from_user = reply_user

        mock_bakchod = MagicMock()
        mock_bakchod.username = "replyuser"
        mock_bakchod.pretty_name = "Reply User"
        mock_bakchod.rokda = 50.25

        mock_bakchod_dao.get_or_create_bakchod_from_tg_user.return_value = mock_bakchod

        import asyncio

        asyncio.run(rokda.handle(mock_update, mock_context))

        assert mock_update.message.reply_text.called


def test_rokda_generate_response():
    """Test rokda response generation."""
    mock_bakchod = MagicMock()
    mock_bakchod.username = "testuser"
    mock_bakchod.pretty_name = "Test User"
    mock_bakchod.rokda = 123.456

    response = rokda.generate_rokda_response(mock_bakchod)

    assert "₹okda" in response
    assert "123.46" in response


def test_version_handle(mock_update, mock_context):
    """Test version handler."""
    with (
        patch("src.bot.handlers.version.dc") as _mock_dc,
        patch("src.bot.handlers.version.util") as _mock_util,
        patch("src.bot.handlers.version.version") as mock_version,
    ):
        mock_version.get_version.return_value = {
            "semver": "1.0.0",
            "git_commit_id": "abc123",
            "git_commit_message": "Test commit",
            "git_commit_time": "2024-01-01",
            "time_service_started": "2024-01-01 00:00:00",
            "pretty_uptime": "1dh 2dm 3ds",
        }

        import asyncio

        from src.bot.handlers import version as version_handler

        asyncio.run(version_handler.handle(mock_update, mock_context))

        assert mock_update.message.reply_text.called
