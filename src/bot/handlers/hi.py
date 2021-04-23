from loguru import logger
from telegram import Update
from domain import dc, util
import random
import datetime


def handle(update: Update, context):

    if util.is_admin_tg_user(update.message.from_user):
        dc.log_command_usage("hi", update)
        update.message.reply_text(random_reply())


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]