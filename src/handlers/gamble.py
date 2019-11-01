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
    random_bakchod = bakchod_util.get_bakchod_random()

    try:
        rokda = bakchod.rokda
    except:
        response = "I don't know you yet... come back later!"
        return response

    if rokda > 50:

        roll = random.random()
        logger.info("roll=%s", roll)

        if roll > 0.98:
            response = "HOLY CRAP! You won! +200 ₹okda"
            rokda = rokda + 200
        elif roll > 0.95:
            response = "OMG! You won! +100 ₹okda"
            rokda = rokda + 100
        elif roll > 0.90:
            response = "You ballin now fam. just won 50 ₹okda"
            rokda = rokda + 50
        elif roll > 0.85:
            response = "You won 50 ₹okda and gifted 15 to {}".format(random_bakchod.username)
            rokda = rokda + 35
            random_bakchod.rokda += 15
        elif roll > 0.70:
            response = "You won +20 ₹okda... this is pretty good tbh!"
            rokda = rokda + 20
        elif roll > 0.50:
            response = "Boond boond se sagar banta... You won! +10 ₹okda"
            rokda = rokda + 10
        elif roll > 0.25:
            response = "{} brought you chai and you tipped him 10 ₹okda".format(random_bakchod.username)
            rokda = rokda - 10
            random_bakchod.rokda += 10
        elif roll > 0.20:
            response = "You got drunk at the bar and drove back home... and also got a chalan of 30 ₹okda"
            rokda = rokda - 30
        elif roll > 0.15:
            response = "No win / no loss... but you still paid entry fee of 50 ₹okda!"
            rokda = rokda - 50
        elif roll > 0.03:
            response = "You actually won... but while leaving the casio you got mugged by {} and lost 70 ₹okda!".format(random_bakchod.username)
            rokda = rokda - 70
            random_bakchod.rokda += 70
        elif roll > 0.01:
            response = "You lost your entire fortune (and Paul's Kwid) to {}. Gambling can suck".format(random_bakchod.username)
            random_bakchod += rokda
            rokda = 5
        else:
            response = "CBI Raided ChaddiInc... That 150 you just won was derokdatized!"
            rokda = rokda - 150

        # Close their accounts at 0 if they're in negatives
        if (rokda < 0):
            rokda = 0
            response = "You're bankrupt with 0 ₹okda, enroll into ChaddiInc Narega!"

        bakchod.rokda = rokda
        bakchod_util.set_bakchod(bakchod)
    
    else:
        response = "Sorry you need atleast 50 ₹okda to gamble! Come back later..."

    return(response)
