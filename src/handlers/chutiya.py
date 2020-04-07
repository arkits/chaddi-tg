from loguru import logger
from util import util
import random
from telegram import ParseMode
import json


def handle(update, context):

    util.log_chat("chutiya", update)

    response = None

    try:
        logger.info("[chutiya]: from user {} in group {}", update.message.from_user['username'], update.message.chat.title)

        if(update.message.reply_to_message):
            og_from = update.message.reply_to_message.from_user
        else:
            og_from = update.message.from_user

        og_sender = extract_pretty_name(og_from)

        if og_sender != config.bot_username:
            update.message.reply_to_message.reply_text("{} is a \n{}".format(og_sender, acronymify('chutiya')))
        else:
            sticker_to_send = 'CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE'
            update.message.reply_sticker(sticker=sticker_to_send)
    except Exception as e:
        logger.error(
            "[chutiya] Caught Error! e={} \n update.message={} ", e, update.message
        )
        response = "bhak bc"

    update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN) 


def extract_pretty_name(from_user):

    if from_user["username"]:
        from_user = "@" + from_user["username"]
    elif from_user["firstname"]:
        from_user = from_user["firstname"]

    return from_user

# makes every word an acronym
def acronymify(word):
    response = str()

    for letter in word:
        response += "\n {} = `{}`".format(letter.upper(), pick_a_word(letter).title())

    return response

# throws a random word that starts with letter
def pick_a_word(letter):
    verbLookupTable = "src/resources/verbPastLookup.json"
    words = list()
    with open(verbLookupTable) as fp:
        data = json.load(fp)
        words = [x for x in data[0].values() if x.startswith(letter)]
    return random.choice(words)