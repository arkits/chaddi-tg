from unittest.mock import AsyncMock, patch

import pytest

from src.domain import tg_logger


@pytest.mark.anyio
async def test_log_success():
    """Test logging message to Telegram successfully."""
    with patch("src.domain.tg_logger.bot") as mock_bot:
        mock_bot_instance = AsyncMock()
        mock_bot.get_bot_instance.return_value = mock_bot_instance

        await tg_logger.log("Test message")

        mock_bot_instance.send_message.assert_called_once()


@pytest.mark.anyio
async def test_log_long_message_truncated():
    """Test that long messages are truncated to 4096 characters."""
    with patch("src.domain.tg_logger.bot") as mock_bot:
        mock_bot_instance = AsyncMock()
        mock_bot.get_bot_instance.return_value = mock_bot_instance

        long_message = "x" * 5000
        await tg_logger.log(long_message)

        mock_bot_instance.send_message.assert_called_once()
        _, kwargs = mock_bot_instance.send_message.call_args
        assert len(kwargs["text"]) == 4096


@pytest.mark.anyio
async def test_log_bot_instance_none():
    """Test logging when bot instance is None."""
    with patch("src.domain.tg_logger.bot") as mock_bot:
        mock_bot.get_bot_instance.return_value = None

        with patch("src.domain.tg_logger.logger") as mock_logger:
            await tg_logger.log("Test message")

            mock_logger.error.assert_called_once()


@pytest.mark.anyio
async def test_log_send_message_error():
    """Test logging when send_message raises an error."""
    with patch("src.domain.tg_logger.bot") as mock_bot:
        mock_bot_instance = AsyncMock()
        mock_bot_instance.send_message.side_effect = Exception("Send failed")
        mock_bot.get_bot_instance.return_value = mock_bot_instance

        with patch("src.domain.tg_logger.logger") as mock_logger:
            await tg_logger.log("Test message")

            mock_logger.error.assert_called_once()
