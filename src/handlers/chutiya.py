from loguru import logger
from util import util, config
import random
from telegram import ParseMode
import json

chaddi_config = config.get_config()

BOT_USERNAME = "@" + chaddi_config["bot_username"]


def handle(update, context):

    util.log_chat("chutiya", update)

    response = None

    try:

        if update.message.reply_to_message:
            og_from = update.message.reply_to_message.from_user
        else:
            og_from = update.message.from_user

        og_sender = util.extract_pretty_name(og_from)

        if og_sender != BOT_USERNAME:
            update.message.reply_to_message.reply_text(
                text="{} is a {}".format(og_sender, acronymify("chutiya")),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            # DON'T INSULT CHADDI!
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            update.message.reply_sticker(sticker=sticker_to_send)

    except Exception as e:
        logger.error(
            "[chutiya] Caught Error! e={} \n update.message={} ", e, update.message
        )
        update.message.reply_text(text="bhak bc")


# makes every word an acronym
def acronymify(word):
    response = str()

    for letter in word:
        response += "\n {} = `{}`".format(letter.upper(), pick_a_word(letter).title())

    return response


# throws a random word that starts with letter
def pick_a_word(letter):
    words = list()
    verbLookupTable = util.get_verbLookupTable()
    words = [x for x in verbLookupTable[0].values() if x.startswith(letter)]
    return random.choice(words)
