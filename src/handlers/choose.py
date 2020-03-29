from loguru import logger
from util import util
import random
from telegram import ParseMode


def handle(update, context):

    util.log_chat("choose", update)

    response = None

    try:
        random_choice = choose_engine(update.message)
        response = "I choose... " + random_choice + "!"
        logger.info(
            "[choose] random_choice={} choices={}", random_choice, update.message.text
        )
    except Exception as e:
        logger.error(
            "[choose] Caught Error! e={} \n update.message={} ", e, update.message
        )
        response = """
Couldn't understand that... here is a sample
`/choose a,b,c`
        """

    update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)


def choose_engine(message):
    message = message["text"].split(",")
    return random.choice(message[1:])
