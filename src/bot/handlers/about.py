from telegram import Update
from telegram.parsemode import ParseMode
from src.domain import dc, util
from src.db import Bakchod, bakchod_dao


def handle(update: Update, context):

    dc.log_command_usage("about", update)

    if update.message.reply_to_message:
        b = bakchod_dao.get_or_create_bakchod_from_tg_user(
            update.message.reply_to_message.from_user
        )
    else:
        b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

    update.message.reply_text(
        text=generate_about_response(b), parse_mode=ParseMode.HTML
    )


def generate_about_response(bakchod: Bakchod):

    about_response = (
        "<b>About " + util.extract_pretty_name_from_bakchod(bakchod) + ":</b> \n"
    )
    about_response = about_response + "~ ID: <code>{}</code> \n".format(bakchod.tg_id)
    about_response = about_response + "~ ₹okda: <code>{}</code> \n".format(
        round(bakchod.rokda, 2)
    )

    return about_response
