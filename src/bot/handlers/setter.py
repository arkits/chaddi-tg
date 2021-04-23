from typing import List
from loguru import logger
from telegram.user import User
from src.db import Bakchod
from src.domain import util, dc
from telegram import ParseMode
from telegram import Update


def handle(update: Update, context):

    dc.log_command_usage("set", update)

    message = update.message.text
    message = message.split(" ")

    if update.message.reply_to_message:
        for_bakchod = update.message.reply_to_message.from_user
    else:
        for_bakchod = update.message.from_user

    og_bakchod = update.message.from_user

    response = parse_request(message, for_bakchod, og_bakchod, update)

    update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)


def parse_request(
    request: List[str], for_bakchod: User, og_bakchod: User, tg_update: Update
) -> str:

    try:
        set_type = request[1]
    except IndexError:
        response = "❔ Please include what you want to set"
        return response

    if set_type.lower() == "rokda":

        try:
            rokda_to_set = float(request[2])
        except IndexError:
            response = "Please include rokda to set - `/set rokda 1337`"
            return response

        if util.is_admin_tg_user(og_bakchod):
            set_reponse = set_bakchod_rokda(rokda_to_set, for_bakchod)
            response = set_reponse
        else:
            response = "❌ Not allowed to set rokda."

    else:

        response = "❌ Can't set that."

    logger.info("[set] returning response='{}'", response)
    return response


def set_bakchod_rokda(rokda_to_set: float, bakchod_user: User):

    b = Bakchod.get_by_id(bakchod_user.id)

    b.rokda = rokda_to_set
    b.save()

    reponse = "✅ Set {}'s ₹okda to {}!".format(
        util.extract_pretty_name_from_bakchod(b), b.rokda
    )

    return reponse
