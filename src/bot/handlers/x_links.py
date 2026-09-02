import io
import re

import httpx
from loguru import logger
from telegram import InputMediaPhoto, InputMediaVideo, Update
from telegram.constants import MessageLimit
from telegram.ext import ContextTypes

# FxEmbed's public API - no key, no account. Swap this for a self-hosted
# FxEmbed worker if the public instance ever goes the way of xcancel.
FX_API_HOST = "https://api.fxtwitter.com"

X_STATUS_URL_REGEX = re.compile(
    r"https?://(?:www\.|mobile\.)?(?:twitter|x)\.com"
    r"/(?P<name>[A-Za-z0-9_]{1,15})/status(?:es)?/(?P<id>\d+)",
    re.IGNORECASE,
)

# Telegram refuses uploads over 50MB, so pick a video variant comfortably under it
MAX_MEDIA_BYTES = 45 * 1024 * 1024
# A media group can hold at most 10 items
MAX_MEDIA_GROUP = 10

HTTP_TIMEOUT = 30.0
MEDIA_TIMEOUT = 120.0


def extract_tweet_ref(message_text: str) -> tuple[str, str] | None:
    """Pull the (screen_name, tweet_id) out of the first x.com status link."""
    match = X_STATUS_URL_REGEX.search(message_text)
    if not match:
        return None

    return match.group("name"), match.group("id")


async def fetch_tweet(screen_name: str, tweet_id: str) -> dict | None:
    """Fetch tweet metadata from FxEmbed. Returns None if it can't be had."""
    # FxEmbed resolves the tweet from the id alone, but passing the handle keeps
    # the request identical to the link that was shared
    url = f"{FX_API_HOST}/{screen_name}/status/{tweet_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"User-Agent": "chaddi-tg"},
                follow_redirects=True,
                timeout=HTTP_TIMEOUT,
            )

        if response.status_code != 200:
            logger.warning(f"[x_links] fx api returned status {response.status_code}")
            return None

        payload = response.json()
        tweet = payload.get("tweet")

        if not tweet:
            logger.warning(f"[x_links] fx api had no tweet - message={payload.get('message')}")
            return None

        return tweet
    except Exception as e:
        logger.error(f"[x_links] error fetching tweet {tweet_id} - {e}")
        return None


def humanize_count(count: int) -> str:
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M".replace(".0M", "M")
    if count >= 1_000:
        return f"{count / 1_000:.1f}K".replace(".0K", "K")
    return str(count)


def build_caption(tweet: dict, limit: int) -> str:
    """Render the tweet as text, trimming the tweet body to fit within limit."""
    author = tweet.get("author") or {}
    name = author.get("name") or author.get("screen_name") or "unknown"
    screen_name = author.get("screen_name")

    header = f"{name} (@{screen_name})" if screen_name else name

    stats = []
    for emoji, key in (("❤️", "likes"), ("🔁", "retweets"), ("💬", "replies")):
        count = tweet.get(key)
        if count:
            stats.append(f"{emoji} {humanize_count(count)}")

    quote = tweet.get("quote") or {}
    quote_author = (quote.get("author") or {}).get("screen_name")
    quote_line = f"↪️ quoting @{quote_author}: {quote.get('text') or ''}".strip() if quote else ""

    body = tweet.get("text") or ""

    # Everything except the tweet body is small and fixed - give the body whatever
    # room is left over rather than truncating the header or the stats
    fixed = [part for part in (header, quote_line, " · ".join(stats)) if part]
    overhead = len("\n\n".join(fixed)) + len("\n\n")
    room = limit - overhead

    if room < 0:
        # Pathological, but never emit something Telegram will reject
        return "\n\n".join(fixed)[:limit]

    if len(body) > room:
        body = body[: max(room - 1, 0)].rstrip() + "…"

    parts = [header]
    if body:
        parts.append(body)
    if quote_line:
        parts.append(quote_line)
    if stats:
        parts.append(" · ".join(stats))

    return "\n\n".join(parts)


def pick_video_url(media_item: dict) -> str | None:
    """Pick the highest quality mp4 that should fit under Telegram's upload cap."""
    duration = media_item.get("duration") or 0
    best_url = None
    best_bitrate = -1

    for variant in media_item.get("variants") or []:
        if variant.get("content_type") != "video/mp4":
            continue

        bitrate = variant.get("bitrate") or 0

        # bits/s * s / 8 = bytes. With no duration we can't estimate, so take it
        # on faith and let the content-length check downstream catch it
        if duration and (bitrate * duration / 8) > MAX_MEDIA_BYTES:
            continue

        if bitrate > best_bitrate:
            best_bitrate = bitrate
            best_url = variant.get("url")

    return best_url or media_item.get("url")


def media_url_for(media_item: dict) -> str | None:
    if media_item.get("type") == "video":
        return pick_video_url(media_item)

    return media_item.get("url")


async def download_media(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=MEDIA_TIMEOUT)
            response.raise_for_status()

        content = response.content

        if len(content) > MAX_MEDIA_BYTES:
            logger.warning(f"[x_links] media too large to upload - {len(content)} bytes")
            return None

        return content
    except Exception as e:
        logger.error(f"[x_links] error downloading media {url} - {e}")
        return None


async def reply_with_media(update: Update, tweet: dict, media_items: list[dict]) -> bool:
    """Upload the tweet's media as a reply. Returns False if nothing could be sent."""
    downloaded = []

    for media_item in media_items[:MAX_MEDIA_GROUP]:
        url = media_url_for(media_item)
        if not url:
            continue

        content = await download_media(url)
        if content is None:
            continue

        downloaded.append((media_item, content))

    if not downloaded:
        return False

    caption = build_caption(tweet, MessageLimit.CAPTION_LENGTH)

    if len(downloaded) == 1:
        media_item, content = downloaded[0]

        if media_item.get("type") == "video":
            await update.message.reply_video(video=io.BytesIO(content), caption=caption)
        else:
            await update.message.reply_photo(photo=io.BytesIO(content), caption=caption)

        return True

    group = []
    for index, (media_item, content) in enumerate(downloaded):
        # Only the first item carries a caption - Telegram shows it for the album
        item_caption = caption if index == 0 else None

        if media_item.get("type") == "video":
            group.append(InputMediaVideo(media=io.BytesIO(content), caption=item_caption))
        else:
            group.append(InputMediaPhoto(media=io.BytesIO(content), caption=item_caption))

    await update.message.reply_media_group(media=group)

    return True


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text

    if not message_text:
        return

    ref = extract_tweet_ref(message_text)
    if ref is None:
        return

    screen_name, tweet_id = ref
    logger.info(f"[x_links] detected x.com status link - {screen_name}/{tweet_id}")

    tweet = await fetch_tweet(screen_name, tweet_id)

    if tweet is None:
        # Fall back to an fxtwitter link so Telegram can at least unfurl a preview
        fallback_url = f"https://fxtwitter.com/{screen_name}/status/{tweet_id}"
        logger.info(f"[x_links] falling back to link preview - {fallback_url}")
        await update.message.reply_text(fallback_url)
        return

    media_items = ((tweet.get("media") or {}).get("all")) or []

    try:
        if media_items and await reply_with_media(update, tweet, media_items):
            logger.info(f"[x_links] replied with {len(media_items)} media item(s)")
            return
    except Exception as e:
        logger.error(f"[x_links] error replying with media - {e}")

    # No media, or the media couldn't be sent - the text is still worth having
    await update.message.reply_text(
        build_caption(tweet, MessageLimit.MAX_TEXT_LENGTH),
        disable_web_page_preview=True,
    )
    logger.info(f"[x_links] replied with tweet text - {screen_name}/{tweet_id}")
