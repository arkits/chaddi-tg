import re

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

X_URL_REGEX = re.compile(
    r"https?://(?:www\.)?x\.com(?=$|[/?#\s])(?P<suffix>(?:[/?#][^\s<]*)?)",
    re.IGNORECASE,
)
TRAILING_PUNCTUATION = ".,!?;:)]}"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text

    if not message_text:
        return

    match = X_URL_REGEX.search(message_text)
    if not match:
        return

    suffix = match.group("suffix").rstrip(TRAILING_PUNCTUATION)
    xcancel_url = f"http://xcancel.com{suffix}"

    logger.info(f"[x_links] converted x.com link to: {xcancel_url}")
    await update.message.reply_text(xcancel_url)
