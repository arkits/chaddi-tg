from telegram.ext import CallbackContext
from telegram import Update, Message
from loguru import logger
from telegram.parsemode import ParseMode
from src.domain import dc, util
from src.db import Bakchod, bakchod_dao


def handle(update: Update, context: CallbackContext):

    try:

        dc.log_command_usage("about", update)

        username = parse_username(update.message.text)
        logger.info("[about] username='{}'", username)

        if username is None:

            # handle based on context
            if update.message.reply_to_message:
                b = bakchod_dao.get_or_create_bakchod_from_tg_user(
                    update.message.reply_to_message.from_user
                )
            else:
                b = bakchod_dao.get_or_create_bakchod_from_tg_user(
                    update.message.from_user
                )

        else:

            # search for bakchod by username
            b = bakchod_dao.get_bakchod_by_username(username)
            if b is None:
                update.message.reply_text(
                    "Kaun hai bee '{}'??? Try <code>/about @username</code>".format(
                        username
                    ),
                    parse_mode=ParseMode.HTML,
                )
                return

        update.message.reply_text(
            text=generate_about_response(b), parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error("Caught Exception in about.handle - e={}", e)


def generate_about_response(bakchod: Bakchod):

    about_response = (
        "<b>About " + util.extract_pretty_name_from_bakchod(bakchod) + ":</b> \n"
    )
    about_response = about_response + "~ ID: <code>{}</code> \n".format(bakchod.tg_id)
    about_response = about_response + "~ ₹okda: <code>{}</code> \n".format(
        util.pretty_print_rokda(bakchod.rokda)
    )
    about_response = about_response + "~ Last seen: <code>{}</code> \n".format(
        bakchod.lastseen
    )

    return about_response


def parse_username(message: str):

    split_message = message.split(" ")

    if not len(split_message) > 1:
        return None

    username = split_message[1]

    if username.startswith("@"):
        username = username[1:]

    return username