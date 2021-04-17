from datetime import datetime
from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from domain import dc
from db import bakchod
from . import hi, bestie


def all(update: Update, context: CallbackContext) -> None:
    dc.sync_persistence_data(update)

    # Reward rokda to Bakchod
    b = bakchod.get_bakchod_from_update(update)
    b.rokda = reward_rokda(b.rokda)
    b.updated = datetime.now()
    b.save()


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


def reward_rokda(r):

    if (r < 0) or r is None:
        r = 0

    # Egalitarian policy - Poor users get more increment than richer users
    r += 100 / (r + 10) + 1
    r = round(r, 2)

    return r