import datetime
import random

from telegram import Update
from telegram.ext import ContextTypes

from src.domain import dc, util


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, log_to_dc=True):
    if util.is_admin_tg_user(update.message.from_user):
        if log_to_dc:
            dc.log_command_usage("hi", update)

        await update.message.reply_text(random_reply())


def random_reply():
    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]
    return random.choice(replies)
