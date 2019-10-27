#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime
import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)


# Handler /gamble
def handle(bot, update):
    logger.info("/gamble: Handling /gamble request from user '%s' in group '%s'", update.message.from_user['username'], update.message.chat.title)
    
    response = gamble(update.message.from_user['id'])
    
    update.message.reply_text(response)


def gamble(bakchod_id):

    response = ""

    bakchod = bakchod_util.get_bakchod(bakchod_id)

    try:
        rokda = bakchod.rokda
    except:
        response = "I don't know you yet... come back later!"
        return response

    roll = random.random()
    logger.info("roll=%s", roll)

    if roll > 0.99:
        response = "HOLY CRAP! You won! +200 ₹okda"
        rokda = rokda + 200
    elif roll > 0.95:
        response = "OMG! You won! +100 ₹okda"
        rokda = rokda + 100
    elif roll > 0.90:
        response = "You ballin now fam. just won 50 ₹okda"
        rokda = rokda + 50
    elif roll > 0.70:
        response = "You won +20 ₹okda... this is pretty good tbh!"
        rokda = rokda + 20
    elif roll > 0.50:
        response = "Boond boond se sagar banta... You won! +10 ₹okda"
        rokda = rokda + 10
    elif roll > 0.25:
        response = "Cr brought you chai and you tipped him 10 ₹okda"
        rokda = rokda - 10
    elif roll > 0.20:
        response = "You got drunk bar and drove back home... and also got a chalan of 30 ₹okda"
        rokda = rokda - 30
    elif roll > 0.15:
        response = "No win / no loss... but you still paid entry fee of 50 ₹okda!"
        rokda = rokda - 50
    elif roll > 0.07:
        response = "You actually won... but while leaving the casio you got mugged by cr and lost 70 ₹okda!"
        rokda = rokda - 70
    else:
        response = "CBI Raided ChaddiInc... That 150 you just was derokdatized!"
        rokda = rokda - 150

    bakchod.rokda = rokda
    bakchod_util.set_bakchod(bakchod)

    return(response)
