from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

# xcancel.com shut down, so there's nowhere to redirect x.com links to right now.
# Flip this back to True once a replacement mirror/renderer is wired up.
ENABLED = False


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not ENABLED:
        logger.trace("[x_links] handler is disabled... skipping")
        return
