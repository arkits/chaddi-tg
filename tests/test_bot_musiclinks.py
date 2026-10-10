from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from telegram import Message, Update
from telegram.ext import ContextTypes

from src.bot.handlers import musiclinks
from src.bot.handlers.musiclinks import Song

RICK = Song(title="Never Gonna Give You Up", artist="Rick Astley")
APPLE_URL = "https://music.apple.com/us/album/never-gonna-give-you-up/1559885420?i=1559885421"
YTM_URL = "https://music.youtube.com/watch?v=lYBUbBu4W08"
YT_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


def json_client(routes: dict) -> httpx.AsyncClient:
    """An httpx client that answers each path with the given (status, json-or-text)."""

    def handler(request: httpx.Request) -> httpx.Response:
        status, body = routes.get(request.url.path, (404, {}))
        if isinstance(body, str):
            return httpx.Response(status, text=body)
        return httpx.Response(status, json=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestUrlParsing:
    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=1", "dQw4w9WgXcQ"),
            ("https://youtu.be/kJQP7kiw5Fk?si=x", "kJQP7kiw5Fk"),
            ("https://music.youtube.com/watch?v=lYBUbBu4W08&feature=share", "lYBUbBu4W08"),
            ("https://www.youtube.com/@mkbhd", None),
        ],
    )
    def test_youtube_video_id(self, url, expected):
        assert musiclinks.youtube_video_id(url) == expected

    @pytest.mark.parametrize(
        "url, expected",
        [
            (APPLE_URL, "1559885421"),
            ("https://music.apple.com/us/song/never-gonna-give-you-up/1559523359", "1559523359"),
            ("https://music.apple.com/us/album/whenever-you-need-somebody/1559885420", None),
        ],
    )
    def test_apple_track_id(self, url, expected):
        assert musiclinks.apple_track_id(url) == expected


class TestMatching:
    def test_prefers_an_exact_title_over_a_higher_ranked_remix(self):
        song = Song(title="Blinding Lights", artist="The Weeknd")
        candidates = [
            ("Blinding Lights (Remix)", ["The Weeknd"], "remix"),
            ("Blinding Lights", ["The Weeknd"], "original"),
        ]

        assert musiclinks.best_match(song, candidates) == "original"

    def test_falls_back_to_a_loose_title_match(self):
        candidates = [("Never Gonna Give You Up (2022 Remaster)", ["Rick Astley"], "remaster")]

        assert musiclinks.best_match(RICK, candidates) == "remaster"

    def test_rejects_covers_by_other_artists(self):
        candidates = [("Never Gonna Give You Up", ["Some Cover Band"], "cover")]

        assert musiclinks.best_match(RICK, candidates) is None

    def test_matches_one_of_several_artists(self):
        song = Song(title="Despacito", artist="Luis Fonsi")
        candidates = [("Despacito", ["Luis Fonsi", "Daddy Yankee"], "match")]

        assert musiclinks.best_match(song, candidates) == "match"


@pytest.mark.asyncio
class TestIdentifySong:
    async def test_reads_spotify_page_metadata(self):
        page = (
            '<meta property="og:title" content="Never Gonna Give You Up"/>'
            '<meta name="music:musician_description" content="Rick Astley, Someone Else"/>'
        )
        async with json_client({"/track/4cOd": (200, page)}) as client:
            source, song = await musiclinks.identify_song(
                client, "https://open.spotify.com/intl-de/track/4cOd?si=abc"
            )

        assert source == "spotify"
        assert song == RICK

    async def test_looks_up_apple_tracks_on_itunes(self):
        lookup = {
            "results": [{"kind": "song", "trackName": RICK.title, "artistName": "Rick Astley"}]
        }
        async with json_client({"/lookup": (200, lookup)}) as client:
            source, song = await musiclinks.identify_song(client, APPLE_URL)

        assert (source, song) == ("appleMusic", RICK)

    async def test_apple_album_links_are_not_a_song(self):
        async with json_client({}) as client:
            source, song = await musiclinks.identify_song(
                client, "https://music.apple.com/us/album/whenever-you-need-somebody/1559885420"
            )

        assert (source, song) == ("appleMusic", None)

    async def test_looks_up_deezer_tracks(self):
        track = {"title": "Harder, Better, Faster, Stronger", "artist": {"name": "Daft Punk"}}
        async with json_client({"/track/3135556": (200, track)}) as client:
            source, song = await musiclinks.identify_song(
                client, "https://www.deezer.com/track/3135556"
            )

        assert source == "deezer"
        assert song == Song(title="Harder, Better, Faster, Stronger", artist="Daft Punk")

    async def test_identifies_youtube_music_videos(self):
        ytmusic = MagicMock()
        ytmusic.get_song.return_value = {
            "videoDetails": {
                "title": RICK.title,
                "author": "Rick Astley",
                "musicVideoType": "MUSIC_VIDEO_TYPE_OMV",
            }
        }

        with patch.object(musiclinks, "get_ytmusic", return_value=ytmusic):
            async with json_client({}) as client:
                source, song = await musiclinks.identify_song(client, YT_URL)

        assert (source, song) == ("youtube", RICK)
        ytmusic.get_song.assert_called_once_with("dQw4w9WgXcQ")

    async def test_ignores_youtube_videos_that_are_not_music(self):
        ytmusic = MagicMock()
        ytmusic.get_song.return_value = {
            "videoDetails": {"title": "Me at the zoo", "author": "jawed"}
        }

        with patch.object(musiclinks, "get_ytmusic", return_value=ytmusic):
            async with json_client({}) as client:
                source, song = await musiclinks.identify_song(
                    client, "https://www.youtube.com/watch?v=jNQXAC9IVRw"
                )

        assert (source, song) == ("youtube", None)

    async def test_spotify_playlists_are_not_a_song(self):
        async with json_client({}) as client:
            source, song = await musiclinks.identify_song(
                client, "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
            )

        assert (source, song) == ("unknown", None)


@pytest.mark.asyncio
class TestFindLinks:
    async def test_finds_apple_music_and_strips_tracking(self):
        search = {
            "results": [
                {
                    "trackName": RICK.title,
                    "artistName": "Rick Astley",
                    "trackViewUrl": APPLE_URL + "&uo=4",
                }
            ]
        }
        async with json_client({"/search": (200, search)}) as client:
            url = await musiclinks.find_on_apple_music(client, RICK)

        assert url == APPLE_URL

    async def test_finds_youtube_music(self):
        ytmusic = MagicMock()
        ytmusic.search.return_value = [
            {"title": RICK.title, "artists": [{"name": "Rick Astley"}], "videoId": "lYBUbBu4W08"}
        ]

        with patch.object(musiclinks, "get_ytmusic", return_value=ytmusic):
            assert await musiclinks.find_on_youtube_music(RICK) == YTM_URL

        ytmusic.search.assert_called_once_with(RICK.query, filter="songs", limit=10)

    async def test_keeps_the_shared_link_and_skips_its_own_platform(self):
        with (
            patch.object(musiclinks, "find_on_apple_music", AsyncMock(return_value=APPLE_URL)),
            patch.object(musiclinks, "find_on_youtube_music", AsyncMock(return_value=YTM_URL)),
            patch.object(musiclinks, "find_on_youtube_video", AsyncMock()) as find_video,
        ):
            links = await musiclinks.find_links(MagicMock(), "youtube", YT_URL, RICK)

        find_video.assert_not_awaited()
        assert links == {
            "appleMusic": APPLE_URL,
            "youtubeMusic": YTM_URL,
            "youtube": YT_URL,
            "spotify": "https://open.spotify.com/search/Rick%20Astley%20Never%20Gonna%20Give%20You%20Up",
        }

    async def test_one_failing_platform_does_not_sink_the_rest(self):
        with (
            patch.object(
                musiclinks, "find_on_apple_music", AsyncMock(side_effect=httpx.ReadTimeout("x"))
            ),
            patch.object(musiclinks, "find_on_youtube_music", AsyncMock(return_value=YTM_URL)),
            patch.object(musiclinks, "find_on_youtube_video", AsyncMock(return_value=YT_URL)),
        ):
            links = await musiclinks.find_links(MagicMock(), "spotify", "https://sp/1", RICK)

        assert links["appleMusic"] is None
        assert links["youtubeMusic"] == YTM_URL


class TestBuildReply:
    def test_lists_platforms_in_order(self):
        reply = musiclinks.build_reply(
            {"youtube": YT_URL, "spotify": "https://sp", "appleMusic": APPLE_URL}
        )

        assert reply == f"[Apple Music]({APPLE_URL}) | [Spotify](https://sp) | [YouTube]({YT_URL})"

    def test_nothing_to_say_without_real_matches(self):
        assert musiclinks.build_reply({"youtube": YT_URL, "spotify": "https://sp"}) is None


@pytest.mark.asyncio
class TestHandle:
    async def test_ignores_messages_without_text(self, mock_update, mock_context):
        mock_update.message.text = None

        await musiclinks.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_awaited()

    async def test_ignores_messages_without_a_music_link(self, mock_update, mock_context):
        mock_update.message.text = "https://example.com/track/123"

        await musiclinks.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_awaited()

    async def test_replies_with_links_for_a_song(self, mock_update, mock_context):
        mock_update.message.text = f"listen to this {YT_URL} yo"
        links = {"appleMusic": APPLE_URL, "youtubeMusic": YTM_URL, "youtube": YT_URL}

        with (
            patch.object(musiclinks, "identify_song", AsyncMock(return_value=("youtube", RICK))),
            patch.object(musiclinks, "find_links", AsyncMock(return_value=links)) as find_links,
        ):
            await musiclinks.handle(mock_update, mock_context)

        assert find_links.await_args.args[1:] == ("youtube", YT_URL, RICK)
        mock_update.message.reply_text.assert_awaited_once()
        args, kwargs = mock_update.message.reply_text.await_args
        assert "[Apple Music]" in args[0]
        assert kwargs == {"disable_web_page_preview": True, "parse_mode": "Markdown"}

    async def test_stays_quiet_when_no_song_is_identified(self, mock_update, mock_context):
        mock_update.message.text = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

        with (
            patch.object(musiclinks, "identify_song", AsyncMock(return_value=("youtube", None))),
            patch.object(musiclinks, "find_links", AsyncMock()) as find_links,
        ):
            await musiclinks.handle(mock_update, mock_context)

        find_links.assert_not_awaited()
        mock_update.message.reply_text.assert_not_awaited()

    async def test_swallows_errors(self, mock_update, mock_context):
        mock_update.message.text = YT_URL

        with patch.object(musiclinks, "identify_song", AsyncMock(side_effect=RuntimeError("boom"))):
            await musiclinks.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_not_awaited()
