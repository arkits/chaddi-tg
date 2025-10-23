from telegram.ext import ContextTypes
from telegram import Update
from loguru import logger
from src.domain import dc, util
from datetime import datetime
import pytz


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        dc.log_command_usage("superpower", update)

        response = superpower_countdown_calc()

        logger.info("[superpower] Returning response={}", response)

        await update.message.reply_text(response)

    except Exception as e:
        logger.error("Caught Exception in superpower.handle - e={}", e)


# Calculates timedelta between current time and Dec 31st 2019 IST.
def superpower_countdown_calc():

    ist = pytz.timezone("Asia/Kolkata")

    # Current time in IST
    now = datetime.now(ist)

    # Dec 31 in IST
    superpower_day = datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0)
    superpower_day = ist.localize(superpower_day)

    # Get timedelta
    td = superpower_day - now

    if td.total_seconds() > 0:
        response = (
            "🇮🇳🙏 Time Until Super Power™️: "
            + util.pretty_time_delta(td.total_seconds())
            + " 🙏🇮🇳"
        )
    else:
        td = now - superpower_day
        response = (
            "🇮🇳🙏 WE INVANT SUPER POWER 🙏🇮🇳 \n Time Since: "
            + util.pretty_time_delta(td.total_seconds())
        )

    return response
