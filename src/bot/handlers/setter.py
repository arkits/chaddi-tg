import math

from loguru import logger
from telegram import Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.db import Bakchod, group_dao
from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dc.log_command_usage("set", update)

    message = update.message.text
    message = message.split(" ")

    if update.message.reply_to_message:
        for_bakchod = update.message.reply_to_message.from_user
    else:
        for_bakchod = update.message.from_user

    og_bakchod = update.message.from_user

    response = parse_request(message, for_bakchod, og_bakchod, update)

    logger.info("[set] returning response='{}'", response)

    await update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)


def parse_request(
    request: list[str], for_bakchod: User, og_bakchod: User, tg_update: Update
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

        if not math.isfinite(rokda_to_set):
            response = set_bakchod_rokda(0, og_bakchod)
            return "Yeh dekho chutiyapa chal ra hai. " + response

        if util.is_admin_tg_user(og_bakchod):
            set_response = set_bakchod_rokda(rokda_to_set, for_bakchod)
            return set_response
        else:
            return "❌ Not allowed to set rokda."

    elif set_type.lower() in ["goodmorning", "gm"]:
        # Check admin (assuming util.is_admin_tg_user checks for bot admin,
        # but maybe we want group admin? The user didn't specify.
        # For now, let's stick to bot admin or just allow it for testing if needed.
        # But usually settings are restricted. I'll use is_admin_tg_user for consistency with rokda)
        # Actually, for group settings, it should probably be group admins.
        # But I don't have a helper for that handy. I'll stick to is_admin_tg_user (bot admin) for now as it's safer.

        if not util.is_admin_tg_user(og_bakchod):
            return "❌ Only admins can set this."

        try:
            value = request[2].lower()
        except IndexError:
            return "Please specify on or off - `/set gm on`"

        if value not in ["on", "off"]:
            return "Please specify on or off - `/set gm on`"

        group = group_dao.get_group_from_update(tg_update)
        if not group:
            return "❌ Group not found."

        if value == "on":
            group.metadata["good_morning_enabled"] = True
            response = "✅ Good morning messages enabled!"
        else:
            group.metadata["good_morning_enabled"] = False
            response = "✅ Good morning messages disabled!"

        # Reassign to ensure peewee picks up the change
        group.metadata = group.metadata
        group.save()
        return response

    elif set_type.lower() == "ask":
        if not util.is_admin_tg_user(og_bakchod):
            return "❌ Only admins can set this."

        try:
            value = request[2].lower()
        except IndexError:
            return "Please specify on or off - `/set ask on`"

        if value not in ["on", "off"]:
            return "Please specify on or off - `/set ask on`"

        group = group_dao.get_group_from_update(tg_update)
        if not group:
            return "❌ Group not found."

        # Initialize enabled_commands if it doesn't exist
        if "enabled_commands" not in group.metadata:
            group.metadata["enabled_commands"] = []

        if value == "on":
            if "ask" not in group.metadata["enabled_commands"]:
                group.metadata["enabled_commands"].append("ask")
            response = "✅ /ask command enabled!"
        else:
            if "ask" in group.metadata["enabled_commands"]:
                group.metadata["enabled_commands"].remove("ask")
            response = "✅ /ask command disabled!"

        # Reassign to ensure peewee picks up the change
        group.metadata = group.metadata
        group.save()
        return response

    else:
        return "❌ Can't set that."


def set_bakchod_rokda(rokda_to_set: float, bakchod_user: User):
    b = Bakchod.get_by_id(bakchod_user.id)

    b.rokda = rokda_to_set
    b.save()

    reponse = f"✅ Set {util.extract_pretty_name_from_bakchod(b)}'s ₹okda to {b.rokda}!"

    return reponse
