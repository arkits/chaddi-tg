from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.error import BadRequest, Forbidden

from src.bot.handlers import errors


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object for testing."""
    update = MagicMock(spec=Update)
    update.to_json.return_value = '{"message": "test"}'
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram Context object for testing."""
    context = MagicMock()
    context.error = Exception("Test error")
    return context


class TestErrors:
    @pytest.mark.anyio
    async def test_log_error_with_valid_update(self, mock_update, mock_context):
        """Test error logging with valid update."""
        with patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger:
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(mock_update, mock_context)

            mock_update.to_json.assert_called()
            mock_tg_logger.log.assert_called_once()

    @pytest.mark.anyio
    async def test_log_error_without_update(self):
        """Test error logging without update."""
        mock_context = MagicMock()
        mock_context.error = Exception("No update error")

        with patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger:
            result = await errors.log_error(None, mock_context)  # type: ignore

            mock_tg_logger.log.assert_not_called()
            assert result is None

    @pytest.mark.anyio
    async def test_log_error_with_traceback(self, mock_update, mock_context):
        """Test error logging includes traceback."""
        with patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger:
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(mock_update, mock_context)

            call_args = mock_tg_logger.log.call_args[0][0]
            assert "Test error" in call_args
            assert "Traceback" in call_args

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "error",
        [
            BadRequest("Not enough rights to send text messages to the chat"),
            BadRequest("Have no rights to send a message"),
            BadRequest("Chat not found"),
            Forbidden("Forbidden: bot was kicked from the supergroup chat"),
        ],
    )
    async def test_log_error_skips_alert_when_bot_cant_send(self, mock_update, error):
        """Errors from chats the bot can't post in are logged as warnings, not alerted."""
        mock_context = MagicMock()
        mock_context.error = error

        with patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger:
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(mock_update, mock_context)

            mock_tg_logger.log.assert_not_called()

    @pytest.mark.anyio
    async def test_log_error_alerts_on_other_bad_requests(self, mock_update):
        """Unrelated BadRequest errors still get alerted."""
        mock_context = MagicMock()
        mock_context.error = BadRequest("Message text is empty")

        with patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger:
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(mock_update, mock_context)

            mock_tg_logger.log.assert_called_once()


class TestPostHogErrorCapture:
    @pytest.mark.anyio
    async def test_log_error_sends_exception_to_posthog(self, mock_context):
        update = MagicMock(spec=Update)
        update.to_json.return_value = "{}"
        update.effective_user.id = 42
        update.effective_user.username = "bakchod"
        update.effective_chat.id = -100
        update.effective_chat.type = "supergroup"
        update.effective_chat.title = "Chaddi"

        with (
            patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger,
            patch("src.bot.handlers.errors.analytics") as mock_analytics,
        ):
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(update, mock_context)

        mock_analytics.capture_exception.assert_called_once()
        args, kwargs = mock_analytics.capture_exception.call_args
        assert args[0] is mock_context.error
        assert kwargs["distinct_id"] == "42"
        assert kwargs["properties"]["chat_id"] == "-100"
        assert kwargs["properties"]["source"] == "telegram"

    @pytest.mark.anyio
    async def test_log_error_skips_posthog_for_cant_send_errors(self, mock_update):
        context = MagicMock()
        context.error = Forbidden("bot was kicked from the group chat")

        with (
            patch("src.bot.handlers.errors.tg_logger") as mock_tg_logger,
            patch("src.bot.handlers.errors.analytics") as mock_analytics,
        ):
            mock_tg_logger.log = AsyncMock()
            await errors.log_error(mock_update, context)

        mock_analytics.capture_exception.assert_not_called()
