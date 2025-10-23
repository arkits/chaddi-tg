import random
import traceback

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import config, dc, util

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                await update.message.reply_to_message.reply_text(
                    text="{} is a {}".format(og_sender, acronymify("chutiya")),
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await update.message.reply_text(
                    text="{} is a {}".format(og_sender, acronymify("chutiya")),
                    parse_mode=ParseMode.MARKDOWN,
                )

        else:
            # DON'T INSULT CHADDI!
            sticker_to_send = "CAADAQADrAEAAp6M4Ahtgp9JaiLJPxYE"
            await update.message.reply_sticker(sticker=sticker_to_send)

    except Exception as e:
        logger.error(
            "Caught Error in chutiya.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


# makes every word an acronym
def acronymify(word):
    response = ""

    for letter in word:
        response += f"\n {letter.upper()} = `{pick_a_word(letter).title()}`"

    return response


# throws a random word that starts with letter
def pick_a_word(letter):
    words = list()
    verb_lookup_table = util.get_verb_past_lookup()
    words = [x for x in verb_lookup_table[0].values() if x.startswith(letter)]
    return random.choice(words)
