from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from src.db import Bakchod, bakchod_dao
from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dc.log_command_usage("rokda", update)

        if update.message.reply_to_message:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(
                update.message.reply_to_message.from_user
            )
        else:
            b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

        await update.message.reply_text(text=generate_rokda_response(b))

    except Exception as e:
        logger.error("Caught Exception in rokda.handle - e={}", e)


def generate_rokda_response(bakchod: Bakchod):
    return f"💰 {util.extract_pretty_name_from_bakchod(bakchod)} has {util.pretty_print_rokda(bakchod.rokda)} ₹okda!"
