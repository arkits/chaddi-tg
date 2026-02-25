import json
import re
import tempfile
from pathlib import Path

import httpx
import instaloader
from instaloader import Post
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

INSTAGRAM_URL_REGEX = r"https?://(?:www\.)?instagram\.com/(?:reel|p)/([a-zA-Z0-9_-]+)/?"


async def download_media_via_instaloader(shortcode: str) -> tuple[str | None, str | None]:
    try:
        loader = instaloader.Instaloader()
        post = Post.from_shortcode(loader.context, shortcode)

        caption = post.caption
        if caption:
            caption = caption[:500]

        media_url = post.video_url if post.is_video else post.url
        return media_url, caption
    except Exception as e:
        logger.error(f"[instagram] instaloader error: {e}")
        return None, None


async def download_media_via_api(shortcode: str) -> tuple[str | None, str | None]:
    url = f"https://www.instagram.com/p/{shortcode}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True, timeout=30.0)

            if response.status_code != 200:
                logger.warning(f"[instagram] page fetch returned status {response.status_code}")
                return None, None

            html = response.text

            share_data_match = re.search(r'"share_data":\s*({.*?})\s*[,}]', html)
            if share_data_match:
                share_data = json.loads(share_data_match.group(1))
                media_url = share_data.get("video_url") or share_data.get("image_url")
                caption = share_data.get("caption", "")

                if media_url:
                    return media_url, caption if caption else None

            ld_json_match = re.search(
                r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL
            )
            if ld_json_match:
                try:
                    ld_json = json.loads(ld_json_match.group(1))
                    if isinstance(ld_json, dict):
                        if ld_json.get("@type") == "VideoObject":
                            return ld_json.get("contentUrl"), ld_json.get("description")
                        elif ld_json.get("@type") == "ImageObject":
                            return ld_json.get("contentUrl"), ld_json.get("caption")
                except json.JSONDecodeError:
                    pass

            video_match = re.search(r'"video_url":"([^"]+)"', html)
            if video_match:
                return video_match.group(1).replace("\\/", "/"), None

            image_match = re.search(r'"display_url":"([^"]+)"', html)
            if image_match:
                return image_match.group(1).replace("\\/", "/"), None

            return None, None

    except Exception as e:
        logger.error(f"[instagram] api fallback error: {e}")
        return None, None


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if not message_text:
        return

    match = re.search(INSTAGRAM_URL_REGEX, message_text)
    if not match:
        return

    url = match.group(0)
    shortcode = match.group(1)
    logger.info(f"[instagram] detected instagram link: {url} (shortcode: {shortcode})")

    media_url = None
    caption = None

    media_url, caption = await download_media_via_instaloader(shortcode)

    if not media_url:
        logger.info("[instagram] trying fallback method via direct API")
        media_url, caption = await download_media_via_api(shortcode)

    if not media_url:
        logger.warning("[instagram] could not extract media URL")
        await update.message.reply_text("Could not find media in this Instagram post.")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()

            suffix = ".mp4" if media_url.endswith(".mp4") else ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(response.content)
                temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                if media_url.endswith(".mp4"):
                    await update.message.reply_video(video=f, caption=caption)
                else:
                    await update.message.reply_photo(photo=f, caption=caption)
            logger.info("[instagram] replied with downloaded media")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"[instagram] error downloading media: {e}")
