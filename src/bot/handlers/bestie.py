from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from src.domain import dc

import random
import datetime


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, log_to_dc=True):

    bestie_response_whitelist = [222021705, 148933790]

    if update.message.from_user["id"] in bestie_response_whitelist:

        if log_to_dc:
            dc.log_command_usage("bestie", update)

        await update.message.reply_text(random_reply())


def random_reply():

    replies = [
        "gussa aa ri",
        "nhi ho ra",
        "chid chid ho ra",
        "mere friend ban jao fir se",
        "pukish hora",
        "headache ho ra",
    ]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
