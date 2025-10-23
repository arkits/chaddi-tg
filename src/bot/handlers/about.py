from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Bakchod, bakchod_dao
from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

        else:
            # search for bakchod by username
            b = bakchod_dao.get_bakchod_by_username(username)
            if b is None:
                await update.message.reply_text(
                    f"Kaun hai bee '{username}'??? Try <code>/about @username</code>",
                    parse_mode=ParseMode.HTML,
                )
                return

        await update.message.reply_text(text=generate_about_response(b), parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error("Caught Exception in about.handle - e={}", e)


def generate_about_response(bakchod: Bakchod):
    about_response = "<b>About " + util.extract_pretty_name_from_bakchod(bakchod) + ":</b> \n"
    about_response = about_response + f"~ ID: <code>{bakchod.tg_id}</code> \n"
    about_response = (
        about_response + f"~ ₹okda: <code>{util.pretty_print_rokda(bakchod.rokda)}</code> \n"
    )
    about_response = about_response + f"~ Last seen: <code>{bakchod.lastseen}</code> \n"

    return about_response


def parse_username(message: str):
    split_message = message.split(" ")

    if not len(split_message) > 1:
        return None

    username = split_message[1]

    if username.startswith("@"):
        username = username[1:]

    return username
