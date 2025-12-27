from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers import pic


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
    message.text = "/pic test query"
    message.reply_to_message = None
    message.caption = None
    message.photo = None
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes object for testing."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


@pytest.mark.asyncio
async def test_handle_no_search_query(mock_update, mock_context):
    """Test pic handler without search query."""
    with patch("src.bot.handlers.pic.dc"):
        mock_update.message.text = "/pic"
        mock_update.message.reply_to_message = None
        mock_update.message.caption = None

        await pic.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_handle_search_from_args(mock_update, mock_context):
    """Test pic handler with search query from command args."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
        patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image1.jpg"},
            {"image": "http://example.com/image2.jpg"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)

        with patch("src.bot.handlers.pic.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            mock_requests.get.return_value = mock_response

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_contextlib.ExitStack.return_value.__enter__.return_value = MagicMock()
            mock_update.message.reply_media_group = AsyncMock()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_search_from_reply_text(mock_update, mock_context):
    """Test pic handler with search query from replied message text."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image.jpg"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)

        reply_user = MagicMock(spec=User)
        reply_user.id = 789012

        reply_message = MagicMock(spec=Message)
        reply_message.from_user = reply_user
        reply_message.text = "beautiful sunset"
        reply_message.caption = None

        mock_update.message.reply_to_message = reply_message
        mock_update.message.text = "/pic"

        with (
            patch("src.bot.handlers.pic.requests") as mock_requests,
            patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
        ):
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            mock_requests.get.return_value = mock_response

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_contextlib.ExitStack.return_value.__enter__.return_value = MagicMock()
            mock_update.message.reply_media_group = AsyncMock()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_search_from_caption(mock_update, mock_context):
    """Test pic handler with search query from caption."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image.jpg"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)

        mock_update.message.text = None
        mock_update.message.caption = "/pic mountains"

        with (
            patch("src.bot.handlers.pic.requests") as mock_requests,
            patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
        ):
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            mock_requests.get.return_value = mock_response

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_contextlib.ExitStack.return_value.__enter__.return_value = MagicMock()
            mock_update.message.reply_media_group = AsyncMock()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handle_no_images_found(mock_update, mock_context):
    """Test pic handler when no images are found."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
    ):
        mock_ddgs.return_value.images.return_value = []
        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"

        mock_sent_message = MagicMock()
        mock_sent_message.edit_text = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

        await pic.handle(mock_update, mock_context)

        mock_sent_message.edit_text.assert_called_once_with(
            "No images found for your search query."
        )


@pytest.mark.asyncio
async def test_handle_timeout_fallback(mock_update, mock_context):
    """Test pic handler fallback when media group times out."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
        patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
        patch("builtins.open", create=True) as mock_open,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image.jpg"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)
        mock_os.listdir.return_value = ["image0.jpg"]
        mock_os.path.exists.return_value = True

        from telegram.error import TimedOut

        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=MagicMock())
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_file

        with patch("src.bot.handlers.pic.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"fake image data"
            mock_response.raise_for_status = MagicMock()
            mock_requests.get.return_value = mock_response

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_update.message.reply_media_group = AsyncMock(side_effect=TimedOut())
            mock_update.message.reply_photo = AsyncMock()
            mock_contextlib.ExitStack.return_value.__enter__.side_effect = TimedOut()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_photo.called


@pytest.mark.asyncio
async def test_handle_download_error_continues(mock_update, mock_context):
    """Test pic handler continues when one image download fails."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
        patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image1.jpg"},
            {"image": "http://example.com/image2.jpg"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)
        mock_os.path.exists.return_value = True
        mock_os.makedirs = MagicMock()
        mock_os.listdir.return_value = ["image1.jpg"]

        with (
            patch("src.bot.handlers.pic.requests") as mock_requests,
            patch("builtins.open", create=True) as mock_open,
        ):
            mock_response_success = MagicMock()
            mock_response_success.headers = {"content-type": "image/jpeg"}
            mock_response_success.content = b"fake image data"
            mock_response_success.raise_for_status = MagicMock()

            mock_response_failure = MagicMock()
            mock_response_failure.raise_for_status.side_effect = Exception("Download failed")

            mock_requests.get.side_effect = [mock_response_success, mock_response_failure]

            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=MagicMock())
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_file

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_contextlib.ExitStack.return_value.__enter__.return_value = MagicMock()
            mock_update.message.reply_media_group = AsyncMock()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_handles_different_content_types(mock_update, mock_context):
    """Test pic handler handles different image content types."""
    with (
        patch("src.bot.handlers.pic.dc"),
        patch("src.bot.handlers.pic.DDGS") as mock_ddgs,
        patch("src.bot.handlers.pic.tempfile") as mock_tempfile,
        patch("src.bot.handlers.pic.os") as mock_os,
        patch("src.bot.handlers.pic.contextlib") as mock_contextlib,
    ):
        mock_ddgs.return_value.images.return_value = [
            {"image": "http://example.com/image1.jpg"},
            {"image": "http://example.com/image2.png"},
            {"image": "http://example.com/image3.gif"},
        ]

        mock_tempfile.mkdtemp.return_value = "/tmp/pic_test"
        mock_os.path.join.side_effect = lambda *args: "/".join(args)
        mock_os.path.exists.return_value = True
        mock_os.makedirs = MagicMock()
        mock_os.listdir.return_value = ["image1.jpg", "image2.png", "image3.gif"]

        with (
            patch("src.bot.handlers.pic.requests") as mock_requests,
            patch("builtins.open", create=True) as mock_open,
        ):
            responses = []
            for content_type in ["image/jpeg", "image/png", "image/gif"]:
                mock_response = MagicMock()
                mock_response.headers = {"content-type": content_type}
                mock_response.content = b"fake image data"
                mock_response.raise_for_status = MagicMock()
                responses.append(mock_response)

            mock_requests.get.side_effect = responses

            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(return_value=MagicMock())
            mock_file.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_file

            mock_sent_message = MagicMock()
            mock_sent_message.edit_text = AsyncMock()
            mock_sent_message.delete = AsyncMock()
            mock_update.message.reply_text = AsyncMock(return_value=mock_sent_message)

            mock_contextlib.ExitStack.return_value.__enter__.return_value = MagicMock()
            mock_update.message.reply_media_group = AsyncMock()

            await pic.handle(mock_update, mock_context)

            assert mock_update.message.reply_text.called
