import random

from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, log_to_dc=True):
    if util.is_admin_tg_user(update.message.from_user):
        if log_to_dc:
            dc.log_command_usage("ping", update)

        await update.message.reply_text(random_reply())


def random_reply():
    replies = ["pong", "ping", "pong bsdk", "ping bsdk", "bhaak sale"]
    return random.choice(replies)
