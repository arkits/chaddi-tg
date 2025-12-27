from unittest.mock import MagicMock, patch

import pytest
from telegram import Update

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
            await errors.log_error(mock_update, mock_context)

            call_args = mock_tg_logger.log.call_args[0][0]
            assert "Test error" in call_args
            assert "Traceback" in call_args
