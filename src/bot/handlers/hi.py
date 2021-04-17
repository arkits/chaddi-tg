from loguru import logger
from telegram import Update
from domain import util, config
import random
import datetime

app_config = config.get_config()

admin_ids = app_config.get("TELEGRAM", "TG_ADMIN_USERS")


def handle(update: Update, context):

    if str(update.message.from_user.id) in admin_ids:
        util.log_chat("hi", update)
        update.message.reply_text(random_reply())


def random_reply():

    replies = ["hi", "bc", "mmll", "...", "🙏 NAMASKAR MANDALI 🙏"]

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(replies) - 1)

    return replies[random_int]