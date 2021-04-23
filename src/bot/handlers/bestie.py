from loguru import logger
from src.domain import dc

import random
import datetime


def handle(update, context):

    bestie_response_whitelist = [222021705, 148933790]

    if update.message.from_user["id"] in bestie_response_whitelist:
        dc.log_command_usage("bestie", update)
        update.message.reply_text(random_reply())


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
