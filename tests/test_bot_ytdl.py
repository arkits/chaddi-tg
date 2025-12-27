from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import ytdl


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_handle_success(mock_update, mock_context):
    """Test handler successful download and upload"""
    mock_update.message.text = "/ytdl https://youtube.com/watch?v=test123"

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)
    mock_update.message.chat_id = 12345

    # Mock youtube-dl
    with patch("src.bot.handlers.ytdl.ydl") as mock_ydl:
        mock_ydl.extract_info.return_value = {
            "id": "test123",
            "title": "Test Video Title",
        }

        # Mock multiprocess
        with patch("src.bot.handlers.ytdl.multiprocessing.Process") as mock_process:
            mock_p = MagicMock()
            mock_p.is_alive.return_value = False
            mock_p.join.return_value = None
            mock_process.return_value = mock_p

            # Mock os.listdir
            with patch("src.bot.handlers.ytdl.os.listdir") as mock_listdir:
                mock_listdir.return_value = ["test123.mp4"]

                with patch("src.bot.handlers.ytdl.os.path.join") as mock_join:
                    mock_join.return_value = "/path/to/test123.mp4"

                    with (
                        patch("builtins.open", mock_open(read_data=b"fake video")),
                        patch("src.bot.handlers.ytdl.util.delete_file"),
                    ):
                        await ytdl.handle(mock_update, mock_context)

    mock_update.message.reply_video.assert_called_once()


@pytest.mark.asyncio
async def test_handle_timeout(mock_update, mock_context):
    """Test handler when download times out"""
    mock_update.message.text = "/ytdl https://youtube.com/watch?v=test123"

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    with patch("src.bot.handlers.ytdl.ydl") as mock_ydl:
        mock_ydl.extract_info.return_value = {
            "id": "test123",
            "title": "Test Video",
        }

        with patch("src.bot.handlers.ytdl.multiprocessing.Process") as mock_process:
            mock_p = MagicMock()
            mock_p.is_alive.return_value = True  # Process still running
            mock_p.terminate.return_value = None
            mock_p.join.return_value = None
            mock_process.return_value = mock_p

            await ytdl.handle(mock_update, mock_context)

    mock_message.edit_text.assert_called()
    call_args = mock_message.edit_text.call_args
    assert "cancelled" in call_args.args[0].lower()
