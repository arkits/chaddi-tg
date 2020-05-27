from loguru import logger
from util import util, config
import random
import datetime

chaddi_config = config.get_config()

hi_response_whitelist = chaddi_config["hi_response_whitelist"]


def handle(update, context):

    if update.message.from_user["username"] in hi_response_whitelist:
        util.log_chat("hi", update)
        update.message.reply_text(random_reply())


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
