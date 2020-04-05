from loguru import logger
from util import util

import random
import datetime


def handle(update, context):

    hi_response_whitelist = ["pahagwl", "arkits", "volis2"]

    if update.message.from_user["username"] in hi_response_whitelist:
        util.log_chat("hi", update)
        update.message.reply_text(random_reply())


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
