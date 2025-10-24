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
        dc.log_command_usage("mom2", update)

        initiator_id = update.message.from_user.id
        if initiator_id is None:
            logger.error("[mom2] initiator_id was None!")
            return

        if not util.paywall_user(initiator_id, COMMAND_COST):
            await update.message.reply_text(
                f"Sorry! You don't have enough ₹okda! Each `/mom2` costs {COMMAND_COST} ₹okda.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        protagonist = util.extract_pretty_name_from_tg_user(update.message.from_user)

        message = mom_spacy.extract_target_message(update)
        if message is None:
            logger.info("[mom2] message was None!")
            return

        response = mom_spacy.rake_joke(message, protagonist)

        logger.info("[mom2] returning response='{}'", response)

        if update.message.reply_to_message:
            await update.message.reply_to_message.reply_text(response)
            return
        else:
            await update.message.reply_text(response)
            return

    except Exception as e:
        logger.error(
            "Caught Error in mom.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return
