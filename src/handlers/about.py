from loguru import logger
from util import util
from db import dao
from models.bakchod import Bakchod
from telegram import ParseMode


def handle(update, context):

    util.log_chat("about", update)

    if update.message.reply_to_message:
        query_id = update.message.reply_to_message.from_user["id"]
    else:
        query_id = update.message.from_user["id"]

    bakchod = dao.get_bakchod_by_id(query_id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        dao.insert_bakchod(bakchod)

    update.message.reply_text(
        text=generate_about_response(bakchod), parse_mode=ParseMode.MARKDOWN
    )


def generate_about_response(bakchod):

    about_response = "*About " + util.extract_pretty_name_from_bakchod(bakchod) + ":* \n"
    about_response = about_response + "~ ID: `{}` \n".format(bakchod.id)
    about_response = about_response + "~ ₹okda: `{}` \n".format(round(bakchod.rokda, 2))

    return about_response
