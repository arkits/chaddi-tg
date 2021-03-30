from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi!")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Help!")


def all(update: Update, context: CallbackContext) -> None:
    logger.info("[all] update={}", update.__dict__)
