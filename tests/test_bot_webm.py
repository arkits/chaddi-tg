from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Document, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import webm


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.mark.asyncio
async def test_handle_no_document(mock_update, mock_context):
    """Test handler with no document"""
    mock_update.message.document = None

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_file_name(mock_update, mock_context):
    """Test handler with document but no file name"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = None
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_not_webm_file(mock_update, mock_context):
    """Test handler with non-webm file"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.mp4"
    mock_update.message.document = mock_document

    await webm.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called


def test_build_webm_conversion_response_basic():
    """Test build_webm_conversion_response with basic parameters"""
    result = webm.build_webm_conversion_response("John", "1 minute", "video.webm", None)

    assert "John" in result
    assert "video.webm" in result
    assert "1 minute" in result


def test_build_webm_conversion_response_with_caption():
    """Test build_webm_conversion_response with caption"""
    caption = "This is a caption"
    result = webm.build_webm_conversion_response("Alice", "2 minutes", "test.webm", caption)

    assert "Alice" in result
    assert "test.webm" in result
    assert "2 minutes" in result
    assert caption in result
    assert "------------------------------------" in result


def test_build_webm_conversion_response_empty_caption():
    """Test build_webm_conversion_response with empty caption"""
    result = webm.build_webm_conversion_response("Bob", "30 seconds", "file.webm", "")

    assert "Bob" in result
    assert "file.webm" in result
    assert "30 seconds" in result


@pytest.mark.asyncio
async def test_handle_webm_file_with_conversion_error(mock_update, mock_context):
    """Test handler when ffmpeg conversion fails"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.webm"
    mock_document.file_id = "123"
    mock_update.message.document = mock_document
    mock_update.message.chat_id = 456
    mock_update.message.from_user = MagicMock(spec=User)
    mock_update.message.from_user.id = 789
    mock_update.message.from_user.username = "testuser"
    mock_update.message.caption = None

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    with (
        patch("src.bot.handlers.webm.dc"),
        patch.object(mock_context.bot, "get_file", side_effect=Exception("Download error")),
    ):
        await webm.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once_with("Starting webm conversion (^◡^)")


@pytest.mark.asyncio
async def test_handle_webm_file_logs_command_usage(mock_update, mock_context):
    """Test that handler logs command usage"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "test.webm"
    mock_document.file_id = "file123"
    mock_update.message.document = mock_document
    mock_update.message.chat_id = 789
    mock_update.message.from_user = MagicMock(spec=User)
    mock_update.message.from_user.id = 456
    mock_update.message.from_user.username = "user1"

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    with (
        patch("src.bot.handlers.webm.dc") as mock_dc,
        patch.object(mock_context.bot, "get_file", side_effect=Exception("Test error")),
    ):
        await webm.handle(mock_update, mock_context)

    mock_dc.log_command_usage.assert_called_once_with("webm", mock_update)


@pytest.mark.asyncio
async def test_handle_with_exception_in_outer_try_block(mock_update, mock_context):
    """Test handler when exception occurs in outer try block"""
    mock_update.message = None

    await webm.handle(mock_update, mock_context)

    assert mock_update.message is None


@pytest.mark.asyncio
async def test_handle_webm_file_success(mock_update, mock_context):
    """Test handler with successful conversion"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.webm"
    mock_document.file_id = "testfile123"
    mock_update.message.document = mock_document
    mock_update.message.chat_id = 999
    mock_update.message.from_user = MagicMock(spec=User)
    mock_update.message.from_user.id = 111
    mock_update.message.from_user.username = "testuser"
    mock_update.message.from_user.first_name = "Test"
    mock_update.message.caption = "Test caption"

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_message.delete = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    mock_webm_file = MagicMock()
    mock_webm_file.download_to_drive = AsyncMock()

    with (
        patch("src.bot.handlers.webm.dc"),
        patch.object(mock_context.bot, "get_file", return_value=mock_webm_file),
        patch("subprocess.call", return_value=0),
        patch("src.bot.handlers.webm.util.pretty_time_delta", return_value="5 minutes"),
        patch("src.bot.handlers.webm.util.delete_file"),
        patch("builtins.open"),
    ):
        await webm.handle(mock_update, mock_context)

    mock_message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_webm_file_ffmpeg_failure(mock_update, mock_context):
    """Test handler when ffmpeg conversion returns non-zero code"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "video.webm"
    mock_document.file_id = "failfile"
    mock_update.message.document = mock_document
    mock_update.message.chat_id = 555
    mock_update.message.from_user = MagicMock(spec=User)
    mock_update.message.from_user.id = 777
    mock_update.message.from_user.username = "failuser"
    mock_update.message.from_user.first_name = "Fail"
    mock_update.message.caption = None

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    mock_webm_file = MagicMock()
    mock_webm_file.download_to_drive = AsyncMock()

    with (
        patch("src.bot.handlers.webm.dc"),
        patch.object(mock_context.bot, "get_file", return_value=mock_webm_file),
        patch("subprocess.call", return_value=1),
        patch("src.bot.handlers.webm.util.delete_file"),
    ):
        await webm.handle(mock_update, mock_context)

    mock_message.edit_text.assert_called_once_with(text="(｡•́︿•̀｡) webm conversion failed (｡•́︿•̀｡)")


@pytest.mark.asyncio
async def test_handle_webm_file_with_reply_to_text(mock_update, mock_context):
    """Test handler with a replied-to message"""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "reply_video.webm"
    mock_document.file_id = "replyfile"
    mock_update.message.document = mock_document
    mock_update.message.chat_id = 111
    mock_update.message.from_user = MagicMock(spec=User)
    mock_update.message.from_user.id = 222
    mock_update.message.from_user.username = "replyuser"
    mock_update.message.from_user.first_name = "Reply"
    mock_update.message.caption = None

    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    mock_update.message.reply_text = AsyncMock(return_value=mock_message)

    mock_webm_file = MagicMock()
    mock_webm_file.download_to_drive = AsyncMock()

    with (
        patch("src.bot.handlers.webm.dc"),
        patch.object(mock_context.bot, "get_file", return_value=mock_webm_file),
        patch("subprocess.call", return_value=0),
        patch("src.bot.handlers.webm.util.pretty_time_delta", return_value="10 seconds"),
        patch("src.bot.handlers.webm.util.delete_file"),
        patch("builtins.open"),
    ):
        await webm.handle(mock_update, mock_context)

    assert mock_update.message.reply_text.called
