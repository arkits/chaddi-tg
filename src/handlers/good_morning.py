from loguru import logger
from util import config
import telegram
import random
import datetime

chaddi_config = config.get_config()


def handle(context: telegram.ext.CallbackContext):

    for id in chaddi_config["good_morning_channels"]:

        random_message = random_reply()

        context.bot.send_message(chat_id=id, text=random_message)

        logger.info("[good_morning] posting! id={} msg={}", id, random_message)


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏", "GOOD MORNING"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
