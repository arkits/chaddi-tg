from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import instagram


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
async def test_handle_no_message_text(mock_update, mock_context):
    """Test handler with no message text"""
    mock_update.message.text = None

    await instagram.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called
    assert not mock_update.message.reply_video.called
    assert not mock_update.message.reply_photo.called


@pytest.mark.asyncio
async def test_handle_no_instagram_url(mock_update, mock_context):
    """Test handler with text but no Instagram URL"""
    mock_update.message.text = "Just a regular message without any Instagram links"

    await instagram.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called
    assert not mock_update.message.reply_video.called
    assert not mock_update.message.reply_photo.called


@pytest.mark.asyncio
async def test_handle_reel_url(mock_update, mock_context):
    """Test handler with Instagram reel URL"""
    mock_update.message.text = (
        "Check out this reel: https://www.instagram.com/reel/DRU3OF7DbHJ/?igsh=MTZyZ2x3dDFqdDhlag=="
    )

    with (
        patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class,
        patch("src.bot.handlers.instagram.httpx.AsyncClient") as mock_async_client_class,
    ):
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = "Test caption"
        mock_post.is_video = True
        mock_post.video_url = "https://instagram.com/video.mp4"
        mock_post.url = None

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = b"fake video content"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.bot.handlers.instagram.Path.unlink"):
                await instagram.handle(mock_update, mock_context)

    mock_update.message.reply_video.assert_called_once()


@pytest.mark.asyncio
async def test_handle_post_url(mock_update, mock_context):
    """Test handler with Instagram post URL"""
    mock_update.message.text = "Look at this: https://www.instagram.com/p/DS4bo50DSXI/"

    with (
        patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class,
        patch("src.bot.handlers.instagram.httpx.AsyncClient") as mock_async_client_class,
    ):
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = "Nice photo!"
        mock_post.is_video = False
        mock_post.video_url = None
        mock_post.url = "https://instagram.com/image.jpg"

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = b"fake image content"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.bot.handlers.instagram.Path.unlink"):
                await instagram.handle(mock_update, mock_context)

    mock_update.message.reply_photo.assert_called_once()


@pytest.mark.asyncio
async def test_handle_no_media_url(mock_update, mock_context):
    """Test handler when no media URL is found"""
    mock_update.message.text = "https://www.instagram.com/p/DS4bo50DSXI/"

    with patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class:
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = "Test caption"
        mock_post.is_video = False
        mock_post.video_url = None
        mock_post.url = None

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post):
            await instagram.handle(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once_with(
        "Could not find media in this Instagram post."
    )


@pytest.mark.asyncio
async def test_handle_exception(mock_update, mock_context):
    """Test handler exception handling"""
    mock_update.message.text = "https://www.instagram.com/p/DS4bo50DSXI/"

    with patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class:
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        from instaloader import Post

        with patch.object(Post, "from_shortcode", side_effect=Exception("Network error")):
            await instagram.handle(mock_update, mock_context)

    assert not mock_update.message.reply_text.called
    assert not mock_update.message.reply_video.called
    assert not mock_update.message.reply_photo.called


@pytest.mark.asyncio
async def test_handle_caption_truncation(mock_update, mock_context):
    """Test that long captions are truncated"""
    long_caption = "a" * 1000
    mock_update.message.text = f"https://www.instagram.com/p/DS4bo50DSXI/ - {long_caption}"

    with (
        patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class,
        patch("src.bot.handlers.instagram.httpx.AsyncClient") as mock_async_client_class,
    ):
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = long_caption
        mock_post.is_video = False
        mock_post.video_url = None
        mock_post.url = "https://instagram.com/image.jpg"

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = b"fake image content"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.bot.handlers.instagram.Path.unlink"):
                await instagram.handle(mock_update, mock_context)

    mock_update.message.reply_photo.assert_called_once()
    call_args = mock_update.message.reply_photo.call_args
    assert len(call_args[1]["caption"]) <= 500


@pytest.mark.asyncio
async def test_handle_no_caption(mock_update, mock_context):
    """Test handler with post that has no caption"""
    mock_update.message.text = "https://www.instagram.com/p/DS4bo50DSXI/"

    with (
        patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class,
        patch("src.bot.handlers.instagram.httpx.AsyncClient") as mock_async_client_class,
    ):
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = None
        mock_post.is_video = False
        mock_post.video_url = None
        mock_post.url = "https://instagram.com/image.jpg"

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post):
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = b"fake image content"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.bot.handlers.instagram.Path.unlink"):
                await instagram.handle(mock_update, mock_context)

    mock_update.message.reply_photo.assert_called_once()
    call_args = mock_update.message.reply_photo.call_args
    assert call_args[1]["caption"] is None


@pytest.mark.asyncio
async def test_handle_short_url(mock_update, mock_context):
    """Test handler with short Instagram URL format"""
    mock_update.message.text = "https://www.instagram.com/p/ABC123/"

    with (
        patch("src.bot.handlers.instagram.instaloader.Instaloader") as mock_instaloader_class,
        patch("src.bot.handlers.instagram.httpx.AsyncClient") as mock_async_client_class,
    ):
        mock_loader = MagicMock()
        mock_instaloader_class.return_value = mock_loader

        mock_post = MagicMock()
        mock_post.caption = "Test"
        mock_post.is_video = False
        mock_post.video_url = None
        mock_post.url = "https://instagram.com/image.jpg"

        from instaloader import Post

        with patch.object(Post, "from_shortcode", return_value=mock_post) as mock_from_shortcode:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.content = b"fake image content"

            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value.__aenter__.return_value = mock_client

            with patch("src.bot.handlers.instagram.Path.unlink"):
                await instagram.handle(mock_update, mock_context)

    mock_from_shortcode.assert_called_once_with(mock_loader.context, "ABC123")
