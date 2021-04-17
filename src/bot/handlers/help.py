from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from domain import dc


def handle(update: Update, context: CallbackContext) -> None:
    dc.log_command_usage("help", update)
    update.message.reply_text("Help!")