from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import x_links


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    update.message.reply_video = AsyncMock()
    update.message.reply_media_group = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


def make_tweet(**overrides):
    tweet = {
        "text": "just setting up my twttr",
        "author": {"name": "jack", "screen_name": "jack"},
        "likes": 308285,
        "retweets": 124745,
        "replies": 18003,
        "media": None,
    }
    tweet.update(overrides)
    return tweet


class TestExtractTweetRef:
    def test_extracts_from_x_url(self):
        assert x_links.extract_tweet_ref("see https://x.com/jack/status/20?s=20") == ("jack", "20")

    def test_extracts_from_twitter_url(self):
        assert x_links.extract_tweet_ref("https://twitter.com/jack/status/20") == ("jack", "20")

    def test_extracts_case_insensitively_with_subdomain(self):
        assert x_links.extract_tweet_ref("HTTPS://MOBILE.X.COM/jack/statuses/20") == ("jack", "20")

    def test_ignores_lookalike_domains(self):
        assert x_links.extract_tweet_ref("https://x.com.evil.com/jack/status/20") is None

    def test_ignores_non_status_links(self):
        assert x_links.extract_tweet_ref("https://x.com/jack") is None

    def test_returns_none_without_a_link(self):
        assert x_links.extract_tweet_ref("no links here") is None

    def test_takes_the_first_link_only(self):
        assert x_links.extract_tweet_ref(
            "https://x.com/first/status/1 https://x.com/second/status/2"
        ) == ("first", "1")


class TestBuildCaption:
    def test_includes_author_text_and_stats(self):
        caption = x_links.build_caption(make_tweet(), 1024)

        assert caption == (
            "jack (@jack)\n\njust setting up my twttr\n\n❤️ 308.3K · 🔁 124.7K · 💬 18K"
        )

    def test_omits_missing_stats(self):
        caption = x_links.build_caption(make_tweet(likes=0, retweets=0, replies=0), 1024)

        assert caption == "jack (@jack)\n\njust setting up my twttr"

    def test_includes_quoted_tweet(self):
        tweet = make_tweet(quote={"author": {"screen_name": "elon"}, "text": "cool"})

        assert "↪️ quoting @elon: cool" in x_links.build_caption(tweet, 1024)

    def test_truncates_body_to_fit_the_limit(self):
        caption = x_links.build_caption(make_tweet(text="x" * 2000), 200)

        assert len(caption) <= 200
        assert caption.startswith("jack (@jack)")
        # The stats survive - only the tweet body gets trimmed
        assert "❤️ 308.3K" in caption
        assert "…" in caption


class TestPickVideoUrl:
    def test_picks_the_highest_bitrate_mp4_that_fits(self):
        media_item = {
            "type": "video",
            "url": "https://video.twimg.com/huge.mp4",
            "duration": 60,
            "variants": [
                {"content_type": "application/x-mpegURL", "url": "https://x/pl.m3u8", "bitrate": 0},
                {"content_type": "video/mp4", "url": "https://x/low.mp4", "bitrate": 256000},
                {"content_type": "video/mp4", "url": "https://x/mid.mp4", "bitrate": 2176000},
                # 60s at 25Mbit/s is ~188MB - over Telegram's cap
                {"content_type": "video/mp4", "url": "https://x/huge.mp4", "bitrate": 25128000},
            ],
        }

        assert x_links.pick_video_url(media_item) == "https://x/mid.mp4"

    def test_falls_back_to_the_default_url_without_variants(self):
        media_item = {"type": "video", "url": "https://video.twimg.com/only.mp4"}

        assert x_links.pick_video_url(media_item) == "https://video.twimg.com/only.mp4"

    def test_photos_use_their_own_url(self):
        assert x_links.media_url_for({"type": "photo", "url": "https://pbs/a.jpg"}) == (
            "https://pbs/a.jpg"
        )


class TestHumanizeCount:
    @pytest.mark.parametrize(
        "count,expected",
        [
            (0, "0"),
            (999, "999"),
            (1000, "1K"),
            (1500, "1.5K"),
            (1_000_000, "1M"),
            (86_486_717, "86.5M"),
        ],
    )
    def test_formats_counts(self, count, expected):
        assert x_links.humanize_count(count) == expected


@pytest.mark.asyncio
class TestHandle:
    async def test_ignores_messages_without_text(self, mock_update, mock_context):
        mock_update.message.text = None

        await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_awaited()

    async def test_ignores_messages_without_an_x_link(self, mock_update, mock_context):
        mock_update.message.text = "https://example.com"

        await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_awaited()

    async def test_replies_with_text_for_a_text_only_tweet(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"

        with patch.object(x_links, "fetch_tweet", AsyncMock(return_value=make_tweet())):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once()
        assert "just setting up my twttr" in mock_update.message.reply_text.await_args.args[0]
        mock_update.message.reply_photo.assert_not_awaited()

    async def test_replies_with_a_photo(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(media={"all": [{"type": "photo", "url": "https://pbs/a.jpg"}]})

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=b"jpegbytes")),
        ):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_photo.assert_awaited_once()
        assert (
            "just setting up my twttr"
            in mock_update.message.reply_photo.await_args.kwargs["caption"]
        )
        mock_update.message.reply_text.assert_not_awaited()

    async def test_replies_with_a_video(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(media={"all": [{"type": "video", "url": "https://video/a.mp4"}]})

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=b"mp4bytes")),
        ):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_video.assert_awaited_once()
        mock_update.message.reply_text.assert_not_awaited()

    async def test_replies_with_a_media_group_for_multiple_photos(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(
            media={
                "all": [
                    {"type": "photo", "url": "https://pbs/a.jpg"},
                    {"type": "photo", "url": "https://pbs/b.jpg"},
                ]
            }
        )

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=b"jpegbytes")),
        ):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_media_group.assert_awaited_once()
        group = mock_update.message.reply_media_group.await_args.kwargs["media"]
        assert len(group) == 2
        # Only the first item carries the caption
        assert group[0].caption is not None
        assert group[1].caption is None

    async def test_sends_at_most_ten_media_items(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(
            media={"all": [{"type": "photo", "url": f"https://pbs/{i}.jpg"} for i in range(15)]}
        )

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=b"jpegbytes")),
        ):
            await x_links.handle(mock_update, mock_context)

        group = mock_update.message.reply_media_group.await_args.kwargs["media"]
        assert len(group) == x_links.MAX_MEDIA_GROUP

    async def test_falls_back_to_text_when_media_cannot_be_downloaded(
        self, mock_update, mock_context
    ):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(media={"all": [{"type": "photo", "url": "https://pbs/a.jpg"}]})

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=None)),
        ):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_photo.assert_not_awaited()
        mock_update.message.reply_text.assert_awaited_once()
        assert "just setting up my twttr" in mock_update.message.reply_text.await_args.args[0]

    async def test_falls_back_to_text_when_the_upload_fails(self, mock_update, mock_context):
        mock_update.message.text = "https://x.com/jack/status/20"
        tweet = make_tweet(media={"all": [{"type": "photo", "url": "https://pbs/a.jpg"}]})
        mock_update.message.reply_photo = AsyncMock(side_effect=Exception("telegram is sad"))

        with (
            patch.object(x_links, "fetch_tweet", AsyncMock(return_value=tweet)),
            patch.object(x_links, "download_media", AsyncMock(return_value=b"jpegbytes")),
        ):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once()

    async def test_falls_back_to_an_fxtwitter_link_when_the_api_fails(
        self, mock_update, mock_context
    ):
        mock_update.message.text = "https://x.com/jack/status/20"

        with patch.object(x_links, "fetch_tweet", AsyncMock(return_value=None)):
            await x_links.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_awaited_once_with(
            "https://fxtwitter.com/jack/status/20"
        )


@pytest.mark.asyncio
class TestFetchTweet:
    async def test_returns_the_tweet_payload(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {"code": 200, "tweet": make_tweet()}
        client = AsyncMock()
        client.get.return_value = response

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = client
            tweet = await x_links.fetch_tweet("jack", "20")

        assert tweet["text"] == "just setting up my twttr"
        assert client.get.await_args.args[0] == f"{x_links.FX_API_HOST}/jack/status/20"

    async def test_returns_none_on_a_non_200(self):
        client = AsyncMock()
        client.get.return_value = MagicMock(status_code=404)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = client
            assert await x_links.fetch_tweet("jack", "20") is None

    async def test_returns_none_on_a_transport_error(self):
        client = AsyncMock()
        client.get.side_effect = Exception("connection reset")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = client
            assert await x_links.fetch_tweet("jack", "20") is None


@pytest.mark.asyncio
class TestDownloadMedia:
    async def test_returns_content(self):
        client = AsyncMock()
        client.get.return_value = MagicMock(content=b"bytes", raise_for_status=MagicMock())

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = client
            assert await x_links.download_media("https://pbs/a.jpg") == b"bytes"

    async def test_rejects_oversized_media(self):
        oversized = b"x" * (x_links.MAX_MEDIA_BYTES + 1)
        client = AsyncMock()
        client.get.return_value = MagicMock(content=oversized, raise_for_status=MagicMock())

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value = client
            assert await x_links.download_media("https://video/a.mp4") is None
