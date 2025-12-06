import traceback

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.domain import config, dc, util

from . import mom_spacy

app_config = config.get_config()

BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")

mom_response_blacklist = [BOT_USERNAME]

COMMAND_COST = 200


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("aao", update)

        initiator_id = update.message.from_user.id
        if initiator_id is None:
            logger.error("[aao] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each `/aao` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        target_message = mom_spacy.extract_target_message(update)
        if target_message is None:
            logger.info("[aao] target_message was None!")
            return

        magic_word = util.extract_magic_word(target_message)
        if magic_word is None:
            logger.info("[aao] magic_word was None!")
            return

        support_word = get_support_word()

        response = f"aao {magic_word} {support_word}"
        response = response.lower()

        logger.info("[aao] generated response={}", response)

        if update.message.reply_to_message:
            await update.message.reply_to_message.reply_text(response)
            return
        else:
            await update.message.reply_text(response)
            return

    except Exception as e:
        logger.error(
            "Caught Error in aao.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def get_support_word():
    support_words = ["dikhae", "sikhae", "kare"]

    support_word = util.choose_random_element_from_list(support_words)

    return support_word
