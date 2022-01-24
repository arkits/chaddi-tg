from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from src.domain import dc


def handle(update: Update, context: CallbackContext) -> None:
    dc.log_command_usage("start", update)
    update.message.reply_text("Hi!")
