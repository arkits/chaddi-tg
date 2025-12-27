import re

import httpx
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

# Regex to match common music streaming URLs
# This is a basic regex and can be expanded.
# Matches: spotify, apple music, youtube, youtube music, deezer, tidal, soundcloud, etc.
MUSIC_URL_REGEX = r"(https?://(?:open\.spotify\.com|music\.apple\.com|www\.youtube\.com|youtu\.be|music\.youtube\.com|www\.deezer\.com|www\.soundcloud\.com|listen\.tidal\.com|tidal\.com|play\.anghami\.com)[^\s]+)"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if not message_text:
        return

    # Find the first matching URL
    match = re.search(MUSIC_URL_REGEX, message_text)
    if not match:
        return

    url = match.group(0)
    logger.info(f"[music] detected music link: {url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.song.link/v1-alpha.1/links?url={url}"
            )

            if response.status_code != 200:
                logger.error(
                    f"[music] song.link api error: {response.status_code} - {response.text}"
                )
                return

            data = response.json()

            links_by_platform = data.get("linksByPlatform")
            if not links_by_platform:
                logger.warning("[music] no links found in song.link response")
                return

            reply_lines = []

            # Helper to add link if exists
            def add_link(platform_key, label):
                if platform_key in links_by_platform:
                    link_url = links_by_platform[platform_key].get("url")
                    if link_url:
                        reply_lines.append(f"[{label}]({link_url})")

            # Add preferred platforms
            add_link("appleMusic", "Apple Music")
            add_link("spotify", "Spotify")
            add_link("youtubeMusic", "YouTube Music")
            add_link("youtube", "YouTube")
            # add_link("amazonMusic", "Amazon Music")
            # add_link("deezer", "Deezer")
            # add_link("tidal", "Tidal")
            # add_link("soundcloud", "SoundCloud")

            if reply_lines:
                reply_text = " | ".join(reply_lines)
                await update.message.reply_text(
                    reply_text, disable_web_page_preview=True, parse_mode="Markdown"
                )
                logger.info("[music] replied with converted links")
            else:
                logger.info("[music] no relevant links found to reply with")

    except Exception as e:
        logger.error(f"[music] error handling music link: {e}")
