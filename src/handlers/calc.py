#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import numexpr

# Enable logging
logger = logging.getLogger(__name__)


# Handler calc
def handle(bot, update):

    logger.info("/calc: Handling /calc request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)

    query = update.message.text
    query = query.split(' ')

    try:
        calc_str = ' '.join(query[1:])
        response = calc_engine(calc_str)
    except Exception as e:
        response = str(e)
    finally:
        logger.info("/calc: calc_str='%s' ; response='%s'", calc_str, response)

    update.message.reply_text(response)


def calc_engine(calc_str):

    result = numexpr.evaluate(calc_str)

    return(str(result))
