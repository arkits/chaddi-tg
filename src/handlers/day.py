from loguru import logger
from util import util
import pytz
import datetime
from telegram import ParseMode


def handle(update, context):

    try:
        util.log_chat("day", update)

        response = generate_response()
        logger.info("[day] Generated response={}", response)

        update.message.reply_text(text=response, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(
            "[day] Caught Error! e={} \n update.message={} ", e, update.message
        )


def generate_response():

    ist = pytz.timezone("Asia/Kolkata")

    today = datetime.datetime.now()
    today = ist.localize(today)

    last_day_of_the_year = datetime.datetime(year=today.year, month=12, day=31)
    last_day_of_the_year = ist.localize(last_day_of_the_year)

    response = "<b>Day:</b> <pre>{}/{}</pre>".format(
        today.strftime("%j"), last_day_of_the_year.strftime("%j")
    )

    return response
