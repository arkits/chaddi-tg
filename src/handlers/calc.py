from loguru import logger
from util import util
import requests
import json


# Using math.js web service for expression eval
API_URL = "http://api.mathjs.org/v4/?expr="


def handle(update, context):

    util.log_chat("calc", update)

    query = update.message.text
    query = query.split(" ")

    try:
        calc_str = " ".join(query[1:])
        response = calc_engine(calc_str)
    except Exception as e:
        response = str(e)
    finally:
        logger.info("[calc] calc_str='{}' ; response='{}'", calc_str, response)

    update.message.reply_text(response)


def calc_engine(calc_str):

    query_url = API_URL + requests.utils.quote(calc_str)

    response = requests.request("GET", query_url)
    response = json.loads(response.text)

    return str(response)
