from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from domain import dc
from . import hi, bestie


def all(update: Update, context: CallbackContext) -> None:
    dc.sync_persistence_data(update)


def handle_message_matching(update, context):

    message_text = update.message.text

    if message_text is not None:

        # Handle 'hi' messages
        if "hi" == message_text.lower():
            hi.handle(update, context)

        # Handle bestie messages
        if "bestie" in message_text.lower():
            bestie.handle(update, context)

    return