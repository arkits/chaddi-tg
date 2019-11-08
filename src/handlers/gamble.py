#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import datetime
from util import bakchod_util

# Enable logging
logger = logging.getLogger(__name__)


# Handler /gamble
def handle(bot, update):
    logger.info("/gamble: Handling /gamble request from user '%s' in group '%s'",
                update.message.from_user['username'], update.message.chat.title)

    response = gamble(update.message.from_user['id'])

    update.message.reply_text(response)


def gamble(bakchod_id):

    response = ""

    bakchod = bakchod_util.get_bakchod(bakchod_id)
    # random_bakchod = bakchod_util.get_bakchod(156943244)

    try:
        rokda = bakchod.rokda
    except:
        response = "I don't know you yet... come back later!"
        return response

    if rokda > 50:

        roll = random.random()
        logger.info("roll=%s", roll)

        if roll > 0.98:
            response = "HOLY CRAP! You won! +500 ₹okda"
            rokda = rokda + 500
        elif roll > 0.95:
            response = "OMG! You won! +400 ₹okda"
            rokda = rokda + 400
        elif roll > 0.90:
            response = "You ballin now fam. just won 300 ₹okda"
            rokda = rokda + 300
        elif roll > 0.85:
            response = "You won 200 ₹okda and gifted 15 to {}".format(
                "cr")
            rokda = rokda + 200
            # random_bakchod.rokda += 15
        elif roll > 0.75:
            response = "You won +100 ₹okda... this is pretty good tbh!"
            rokda = rokda + 100
        elif roll > 0.65:
            response = "Boond boond se sagar banta... You won! +50 ₹okda"
            rokda = rokda + 50
        elif roll > 0.55:
            response = "Your wallet got stolen in the local train, good thing ₹okda are digital. Take +1 ₹okda in pity"
            rokda = rokda + 1
        elif roll > 0.45:
            response = "{} brought you chai and you tipped him 100 ₹okda".format(
                "cr")
            rokda = rokda - 100
            # random_bakchod.rokda += 100
        elif roll > 0.35:
            response = "You got drunk at the bar and drove back home... and also got a chalan of 300 ₹okda"
            rokda = rokda - 300
        elif roll > 0.25:
            response = "No win / no loss... but you still paid entry fee of 400 ₹okda!"
            rokda = rokda - 400
        elif roll > 0.15:
            response = "You actually won... but while leaving the casino you got mugged by {} and lost 500 ₹okda!".format(
                "cr")
            rokda = rokda - 500
            # random_bakchod.rokda += 500
        elif roll > 0.01:
            response = "CBI Raided ChaddiInc... That 1000 you just won was derokdatized!"
            rokda = rokda - 1000
        else:
            response = "You lost your entire fortune (and Paul's Kwid) to {}. Gambling can suck!".format(
                "cr")
            # random_bakchod.rokda += rokda
            rokda = 1

        # Close their accounts at 0 if they're in negatives
        if (rokda < 0):
            rokda = 0
            response = "You're bankrupt with 0 ₹okda, enroll into ChaddiInc Narega!"

        bakchod.rokda = rokda
        bakchod_util.set_bakchod(bakchod)
        # bakchod_util.set_bakchod(random_bakchod)

    else:
        response = "Sorry you need atleast 50 ₹okda to gamble! Come back later..."

    return(response)
