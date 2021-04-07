import datetime
from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from db import bakchod
from db import message


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hi!")


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Help!")


def all(update: Update, context: CallbackContext) -> None:

    bakchod.get_bakchod_from_update(update)
    message.log_message_from_update(update)
