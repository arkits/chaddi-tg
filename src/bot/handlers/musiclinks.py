import asyncio
import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, quote, urlparse

import httpx
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from ytmusicapi import YTMusic

# song.link (Odesli) retired its keyless API in 2026, so we resolve links
# ourselves from keyless sources: Spotify page metadata, the iTunes Search API,
# Deezer's public API and YouTube Music via ytmusicapi. Spotify has no keyless
# search, so the Spotify link we post is a search link.

MUSIC_URL_REGEX = re.compile(
    r"https?://(?:open\.spotify\.com|music\.apple\.com|(?:www\.|m\.)?youtube\.com"
    r"|youtu\.be|music\.youtube\.com|(?:www\.)?deezer\.com)[^\s]+",
    re.IGNORECASE,
)

SPOTIFY_TRACK_REGEX = re.compile(r"open\.spotify\.com/(?:intl-[a-z-]+/)?track/([A-Za-z0-9]+)")
DEEZER_TRACK_REGEX = re.compile(r"deezer\.com/(?:[a-z]{2}/)?track/(\d+)")
APPLE_SONG_REGEX = re.compile(r"music\.apple\.com/.*/song/[^/]+/(\d+)")
META_REGEX = '<meta (?:property|name)="{}" content="([^"]*)"'

HTTP_TIMEOUT = 15.0
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; chaddi-tg)"}

_ytmusic = None


@dataclass
class Song:
    title: str
    artist: str

    @property
    def query(self) -> str:
        return f"{self.artist} {self.title}"


def get_ytmusic() -> YTMusic:
    global _ytmusic
    if _ytmusic is None:
        _ytmusic = YTMusic()
    return _ytmusic


def normalize(text: str, keep_extras: bool = False) -> str:
    """Lowercase and keep only letters/digits. Unless keep_extras, also drop
    bracketed extras like (Remastered) and suffixes like "- 2009 Remaster"."""
    text = text.lower()
    if not keep_extras:
        text = re.sub(r"[\(\[].*?[\)\]]", "", text)
        text = re.sub(r"\s+-\s+.*$", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


def is_same_artist(song: Song, artists: list[str]) -> bool:
    want = normalize(song.artist)
    return bool(want) and any(
        got and (want in got or got in want) for got in (normalize(a) for a in artists)
    )


def is_same_title(song: Song, title: str, exact: bool) -> bool:
    if exact:
        return normalize(song.title, keep_extras=True) == normalize(title, keep_extras=True)

    want, got = normalize(song.title), normalize(title)
    return bool(want and got) and (want in got or got in want)


def best_match(song: Song, candidates: list[tuple[str, list[str], str]]) -> str | None:
    """Pick the candidate (title, artists, value) that is the song we asked for.

    An exact title wins over a loose one, so "Blinding Lights" doesn't resolve
    to "Blinding Lights (Remix)" just because the remix ranked higher.
    """
    for exact in (True, False):
        for title, artists, value in candidates:
            if is_same_title(song, title, exact) and is_same_artist(song, artists):
                return value
    return None


def youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0] or None
    if parsed.path == "/watch":
        return (parse_qs(parsed.query).get("v") or [None])[0]
    return None


def apple_track_id(url: str) -> str | None:
    # Album links point at a track with ?i=<track id>
    track_id = (parse_qs(urlparse(url).query).get("i") or [None])[0]
    if track_id:
        return track_id

    match = APPLE_SONG_REGEX.search(url)
    return match.group(1) if match else None


# --- figuring out which song was shared ---


async def song_from_spotify(client: httpx.AsyncClient, track_id: str) -> Song | None:
    response = await client.get(f"https://open.spotify.com/track/{track_id}")
    if response.status_code != 200:
        return None

    title = re.search(META_REGEX.format("og:title"), response.text)
    artist = re.search(META_REGEX.format("music:musician_description"), response.text)
    if not title or not artist:
        return None

    # Multiple artists come through as "A, B" - the first is the main one
    return Song(
        title=html.unescape(title.group(1)),
        artist=html.unescape(artist.group(1)).split(",")[0].strip(),
    )


async def song_from_apple(client: httpx.AsyncClient, track_id: str) -> Song | None:
    response = await client.get("https://itunes.apple.com/lookup", params={"id": track_id})
    if response.status_code != 200:
        return None

    results = response.json().get("results") or []
    track = next((r for r in results if r.get("kind") == "song"), None)
    if not track:
        return None

    return Song(title=track["trackName"], artist=track["artistName"])


async def song_from_deezer(client: httpx.AsyncClient, track_id: str) -> Song | None:
    response = await client.get(f"https://api.deezer.com/track/{track_id}")
    if response.status_code != 200:
        return None

    track = response.json()
    if "error" in track or not track.get("title"):
        return None

    return Song(title=track["title"], artist=track["artist"]["name"])


async def song_from_youtube(video_id: str) -> Song | None:
    details = (await asyncio.to_thread(get_ytmusic().get_song, video_id)).get("videoDetails") or {}

    # Plain YouTube videos have no musicVideoType - don't answer every vlog link
    if not details.get("musicVideoType"):
        return None

    return Song(title=details["title"], artist=details["author"])


async def identify_song(client: httpx.AsyncClient, url: str) -> tuple[str, Song | None]:
    """Work out which platform a link is from and which song it points at."""
    if match := SPOTIFY_TRACK_REGEX.search(url):
        return "spotify", await song_from_spotify(client, match.group(1))

    if "music.apple.com" in url:
        track_id = apple_track_id(url)
        if not track_id:
            return "appleMusic", None
        return "appleMusic", await song_from_apple(client, track_id)

    if match := DEEZER_TRACK_REGEX.search(url):
        return "deezer", await song_from_deezer(client, match.group(1))

    if video_id := youtube_video_id(url):
        platform = "youtubeMusic" if "music.youtube.com" in url else "youtube"
        return platform, await song_from_youtube(video_id)

    return "unknown", None


# --- finding it everywhere else ---


async def find_on_apple_music(client: httpx.AsyncClient, song: Song) -> str | None:
    response = await client.get(
        "https://itunes.apple.com/search",
        params={"term": song.query, "entity": "song", "limit": 10},
    )
    if response.status_code != 200:
        return None

    candidates = [
        (r.get("trackName", ""), [r.get("artistName", "")], r.get("trackViewUrl"))
        for r in response.json().get("results") or []
        if r.get("trackViewUrl")
    ]
    url = best_match(song, candidates)

    # Drop iTunes' affiliate tracking param
    return url.replace("&uo=4", "") if url else None


async def find_on_youtube(song: Song, result_filter: str) -> str | None:
    results = await asyncio.to_thread(
        get_ytmusic().search, song.query, filter=result_filter, limit=10
    )

    candidates = [
        (r.get("title", ""), [a.get("name", "") for a in r.get("artists") or []], r["videoId"])
        for r in results
        if r.get("videoId")
    ]
    return best_match(song, candidates)


async def find_on_youtube_music(song: Song) -> str | None:
    video_id = await find_on_youtube(song, "songs")
    return f"https://music.youtube.com/watch?v={video_id}" if video_id else None


async def find_on_youtube_video(song: Song) -> str | None:
    video_id = await find_on_youtube(song, "videos")
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else None


def spotify_search_url(song: Song) -> str:
    return f"https://open.spotify.com/search/{quote(song.query)}"


async def safely(coro, platform: str) -> str | None:
    try:
        return await coro
    except Exception as e:
        logger.warning(f"[music] {platform} lookup failed: {e}")
        return None


async def find_links(client: httpx.AsyncClient, source: str, url: str, song: Song) -> dict:
    """Links to the song on each platform. The shared link stands in for its own platform."""
    lookups = {
        "appleMusic": lambda: find_on_apple_music(client, song),
        "youtubeMusic": lambda: find_on_youtube_music(song),
        "youtube": lambda: find_on_youtube_video(song),
    }
    lookups.pop(source, None)

    found = await asyncio.gather(*(safely(lookup(), p) for p, lookup in lookups.items()))
    links = dict(zip(lookups, found, strict=True))

    links[source] = url
    links.setdefault("spotify", spotify_search_url(song))

    return links


def build_reply(links: dict) -> str | None:
    labels = (
        ("appleMusic", "Apple Music"),
        ("spotify", "Spotify"),
        ("youtubeMusic", "YouTube Music"),
        ("youtube", "YouTube"),
    )
    parts = [f"[{label}]({links[key]})" for key, label in labels if links.get(key)]

    # Only the shared link and a Spotify search? Nothing worth posting
    if len(parts) < 3:
        return None

    return " | ".join(parts)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if not message_text:
        return

    match = MUSIC_URL_REGEX.search(message_text)
    if not match:
        return

    url = match.group(0)
    logger.info(f"[music] detected music link: {url}")

    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT, headers=HEADERS, follow_redirects=True
        ) as client:
            source, song = await identify_song(client, url)

            if song is None:
                logger.info(f"[music] couldn't identify a song from {source} link")
                return

            logger.info(f"[music] identified {song.artist} - {song.title} from {source}")
            links = await find_links(client, source, url, song)

        reply_text = build_reply(links)
        if not reply_text:
            logger.info("[music] no matches found on other platforms")
            return

        await update.message.reply_text(
            reply_text, disable_web_page_preview=True, parse_mode="Markdown"
        )
        logger.info("[music] replied with converted links")

    except Exception as e:
        logger.error(f"[music] error handling music link: {e}")
