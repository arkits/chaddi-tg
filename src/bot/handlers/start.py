from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dc.log_command_usage("start", update)
    await update.message.reply_text("Hi!")
