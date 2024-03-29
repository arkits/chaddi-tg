import random
from loguru import logger
from telegram import Update
from src.domain import dc, util, config
from telegram import ParseMode
import traceback

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200


def handle(update: Update, context):

    try:

        dc.log_command_usage("chutiya", update)

        reply_to_message = update.message.reply_to_message
        if reply_to_message is not None:
            og_from = update.message.reply_to_message.from_user
        else:
            og_from = update.message.from_user

        og_sender = util.extract_pretty_name_from_tg_user(og_from)
        if og_sender != BOT_USERNAME:
            if reply_to_message is not None:
                update.message.reply_to_message.reply_text(
                    text="{} is a {}".format(og_sender, acronymify("chutiya")),
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                update.message.reply_text(
                    text="{} is a {}".format(og_sender, acronymify("chutiya")),
                    parse_mode=ParseMode.MARKDOWN,
                )

        else:
            # DON'T INSULT CHADDI!
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            update.message.reply_sticker(sticker=sticker_to_send)

    except Exception as e:
        logger.error(
            "Caught Error in chutiya.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


# makes every word an acronym
def acronymify(word):
    response = str()

    for letter in word:
        response += "\n {} = `{}`".format(letter.upper(), pick_a_word(letter).title())

    return response


# throws a random word that starts with letter
def pick_a_word(letter):
    words = list()
    verb_lookup_table = util.get_verb_past_lookup()
    words = [x for x in verb_lookup_table[0].values() if x.startswith(letter)]
    return random.choice(words)
