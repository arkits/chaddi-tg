from loguru import logger
from peewee import Update
from domain import dc, util
from db import Bakchod, bakchod
from telegram import ParseMode


def handle(update: Update, context):

    dc.log_command_usage("rokda", update)

    b = bakchod.get_bakchod_from_update(update)

    update.message.reply_text(
        text=generate_rokda_response(b), parse_mode=ParseMode.MARKDOWN
    )


def generate_rokda_response(bakchod: Bakchod):

    response = "💰 {} has {} ₹okda!".format(
        util.extract_pretty_name_from_bakchod(bakchod), round(bakchod.rokda, 2)
    )

    return response
