from loguru import logger
from telegram import Update
from telegram.ext import CallbackContext
from src.domain import dc

import random
import datetime


def handle(update: Update, context: CallbackContext, log_to_dc=True):

    try:

        if not is_wordle_result(update.message.text):
            return

        if log_to_dc:
            dc.log_command_usage("antiwordle", update)

        logger.info("[antiwordle] detected wordle message={}", update.message.text)

        update.message.reply_text(random_reply())

        try:
            update.message.delete()
        except Exception as e:
            logger.error("[antiwordle] caught error while deleting message={}", e)

    except Exception as e:
        logger.error("Caught Exception in antiworlde.handle - e={}", e)


allowed = set("⬛️🟨🟩")


def is_wordle_result(message_text: str) -> bool:

    if message_text is None:
        return False

    messages_text_lines = message_text.split("\n")

    first_line = messages_text_lines[0]

    if first_line is None:
        return False

    if not first_line.startswith("Wordle"):
        return False

    if not first_line.endswith("/6"):
        return False

    if not len(first_line) > 11:
        return False

    if not len(messages_text_lines) >= 3:
        return False

    # check remaining lines
    for line in messages_text_lines[2:]:
        logger.debug("[antiwordle] checking line={}", line)

        if line is None:
            return False

        if not set(line) <= allowed:
            return False

    return True


def random_reply():

    replies = [
        "KILL ALL WORDLE TARDS 🔫",
        "WORDLE WAALOO TUMAHRI MAA KAA",
        "BHHAAAAAAAAKKKKK TERA WORDLE BSDK",
        "HAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATTTTT",
        "NO ONE CARES ABOUT YOUR WORDLE TARSH",
    ]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]