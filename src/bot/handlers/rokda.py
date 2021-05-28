from loguru import logger
from peewee import Update
from src.domain import dc, util
from src.db import Bakchod, bakchod


def handle(update: Update, context):

    dc.log_command_usage("rokda", update)

    if update.message.reply_to_message:
        b = bakchod.get_or_create_bakchod_from_tg_user(
            update.message.reply_to_message.from_user
        )
    else:
        b = bakchod.get_or_create_bakchod_from_tg_user(update.message.from_user)

    update.message.reply_text(text=generate_rokda_response(b))


def generate_rokda_response(bakchod: Bakchod):

    response = "💰 {} has {} ₹okda!".format(
        util.extract_pretty_name_from_bakchod(bakchod), round(bakchod.rokda, 2)
    )

    return response
