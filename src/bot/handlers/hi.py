from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from src.domain import dc, util
import random
import datetime


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, log_to_dc=True):

    if util.is_admin_tg_user(update.message.from_user):

        if log_to_dc:
            dc.log_command_usage("hi", update)

        await update.message.reply_text(random_reply())


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]
