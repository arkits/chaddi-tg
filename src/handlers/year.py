from loguru import logger
from util import util
import traceback
import datetime
import pytz
import math

FILLED_CHAR = "█"
UNFILLED_CHAR = "—"
MAX_LEN = 23


def handle(update, context):

    try:

        util.log_chat("year", update)

        response = year_progress_response_generator()

        if response is None:
            return

        logger.info("[year] Returning response={}", response)
        update.message.reply_text(response)

    except Exception as e:
        logger.error(
            "Caught Error in year.handle - {} \n {}", e, traceback.format_exc(),
        )


def year_progress_response_generator():

    ist = pytz.timezone("Asia/Kolkata")

    now = datetime.datetime.now(ist)

    start_of_year = datetime.datetime(
        year=now.year, month=1, day=1, hour=0, minute=0, second=0
    )
    start_of_year = ist.localize(start_of_year)

    end_of_year = datetime.datetime(
        year=now.year, month=12, day=31, hour=11, minute=59, second=59
    )
    end_of_year = ist.localize(end_of_year)

    # logger.info("start_of_year={} end_of_year={}", start_of_year, end_of_year)

    td1 = now - start_of_year
    seconds_elapsed_this_year = td1.total_seconds()

    td2 = end_of_year - start_of_year
    total_seconds_this_year = td2.total_seconds()

    # logger.info(
    #     "seconds_elapsed_this_year={} total_seconds_this_year={}",
    #     seconds_elapsed_this_year,
    #     total_seconds_this_year,
    # )

    percent = (seconds_elapsed_this_year / total_seconds_this_year) * 100

    pretty_percent = round(percent, 2)

    progress_bar = generate_progress_bar(pretty_percent)

    response = "{} {}%".format(progress_bar, pretty_percent)

    return response


def generate_progress_bar(percent):

    filled = ""
    unfilled = ""

    filled_bar_range = math.ceil(MAX_LEN * (percent / 100))
    unfilled_bar_range = math.ceil(MAX_LEN * (abs(percent - 100) / 100))

    # logger.info(
    #     "filled_bar_range={} unfilled_bar_range={}",
    #     filled_bar_range,
    #     unfilled_bar_range,
    # )

    for n in range(filled_bar_range):

        filled = filled + FILLED_CHAR

    for n in range(unfilled_bar_range):

        unfilled = unfilled + UNFILLED_CHAR

    progress_bar = "|{}{}|".format(filled, unfilled)

    return progress_bar
