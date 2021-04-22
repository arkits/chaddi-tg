from loguru import logger
from peewee import Update
from domain import dc, util
from db import Bakchod, bakchod
from telegram import ParseMode


def handle(update: Update, context):

    dc.log_command_usage("about", update)

    b = bakchod.get_bakchod_from_update(update)

    update.message.reply_text(
        text=generate_about_response(b), parse_mode=ParseMode.MARKDOWN
    )


def generate_about_response(bakchod: Bakchod):

    about_response = (
        "*About " + util.extract_pretty_name_from_bakchod(bakchod) + ":* \n"
    )
    about_response = about_response + "~ ID: `{}` \n".format(bakchod.tg_id)
    about_response = about_response + "~ ₹okda: `{}` \n".format(round(bakchod.rokda, 2))

    return about_response
