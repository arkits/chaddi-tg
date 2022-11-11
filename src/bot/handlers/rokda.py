from telegram.ext import CallbackContext
from telegram import Update
from loguru import logger
from src.domain import dc, util
from src.db import Bakchod, bakchod_dao


def handle(update: Update, context: CallbackContext):

    try:

        dc.log_command_usage("rokda", update)

        if update.message.reply_to_message:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(
                update.message.reply_to_message.from_user
            )
        else:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

        update.message.reply_text(text=generate_rokda_response(b))

    except Exception as e:
        logger.error("Caught Exception in rokda.handle - e={}", e)


def generate_rokda_response(bakchod: Bakchod):
    return "💰 {} has {} ₹okda!".format(
        util.extract_pretty_name_from_bakchod(bakchod),
        util.pretty_print_rokda(bakchod.rokda),
    )
