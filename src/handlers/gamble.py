#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
import random
from datetime import *
from util import bakchod_util
from util import group_util
from models import bakchod

# Enable logging
logger = logging.getLogger(__name__)


# Handler /gamble
def handle(bot, update):
    logger.info("/gamble: Handling /gamble request from user '%s' in group '%s'",
                update.message.from_user['username'], update.message.chat.title)

    response = gamble(update.message.from_user['id'], update.message.chat['id'])
    logger.info("/gamble: Returning response: '%s'", response)

    update.message.reply_text(response)


def gamble(bakchod_id, chat_id):

    bakchod = bakchod_util.get_bakchod(bakchod_id)

    can_gamble, response = can_bakchod_gamble(bakchod)

    if can_gamble:

        # Get a random_bakchod from the same Group
        group = group_util.get_group(chat_id)
        random_bakchod = get_random_bakchod(group, bakchod_id)

        response, bakchod, random_bakchod = gamble_engine(bakchod, random_bakchod)

        # Update History
        try:
            history = bakchod.history 
        except:
            history = {}
        history['gamble'] = datetime.now()
        bakchod.history = history

        # Update gambler bakchod
        bakchod_util.set_bakchod(bakchod)

        # Update random_bakchod
        if random_bakchod.id != 0:
            bakchod_util.set_bakchod(random_bakchod)

    return(response)


def gamble_engine(bakchod, random_bakchod):

    response = ""

    roll = random.random()
    logger.info("/gamble: roll=%s", roll)

    if roll > 0.98:
        response = "HOLY CRAP! You won! +500 ₹okda"
        bakchod.rokda = bakchod.rokda + 500
    elif roll > 0.95:
        response = "OMG! You won! +400 ₹okda"
        bakchod.rokda = bakchod.rokda + 400
    elif roll > 0.90:
        response = "You ballin now fam. just won 300 ₹okda"
        bakchod.rokda = bakchod.rokda + 300
    elif roll > 0.85:
        response = "You won 200 ₹okda and gifted 15 to {}".format(
            random_bakchod.username)
        bakchod.rokda = bakchod.rokda + 200
        random_bakchod.rokda += 15
    elif roll > 0.75:
        response = "You won +100 ₹okda... this is pretty good tbh!"
        bakchod.rokda = bakchod.rokda + 100
    elif roll > 0.65:
        response = "Boond boond se sagar banta... You won! +50 ₹okda"
        bakchod.rokda = bakchod.rokda + 50
    elif roll > 0.55:
        response = "Your wallet got stolen in the local train, good thing ₹okda are digital. Take +1 ₹okda in pity"
        bakchod.rokda = bakchod.rokda + 1
    elif roll > 0.45:
        response = "{} brought you chai and you tipped him 100 ₹okda".format(
            random_bakchod.username)
        bakchod.rokda = bakchod.rokda - 100
        random_bakchod.rokda += 100
    elif roll > 0.35:
        response = "No win / no loss... but you still paid entry fee of 250 ₹okda!"
        bakchod.rokda = bakchod.rokda - 250
    elif roll > 0.25:
        response = "You got drunk at the bar and drove back home... and also got a chalan of 375 ₹okda"
        bakchod.rokda = bakchod.rokda - 375
    elif roll > 0.15:
        response = "You actually won... but while leaving the casino you got mugged by {} and lost 500 ₹okda!".format(
            random_bakchod.username)
        bakchod.rokda = bakchod.rokda - 500
        random_bakchod.rokda += 500
    elif roll > 0.01:
        response = "CBI Raided ChaddiInc... That 1000 you just won was derokdatized!"
        bakchod.rokda = bakchod.rokda - 1000
    elif roll > 0.001:
        response = "You lost your entire fortune (and Paul's Kwid) to {}. Gambling can suck!".format(
            random_bakchod.username)
        random_bakchod.rokda += bakchod.rokda
        bakchod.rokda = 1

    # Close their accounts at 0 if they're in negatives
    if (bakchod.rokda < 0):
        bakchod.rokda = 0
        response = response + " You're bankrupt with 0 ₹okda, enroll into ChaddiInc Narega!"

    return response, bakchod, random_bakchod


def can_bakchod_gamble(bakchod):

    can_gamble = True
    response = None

    try:
        one_min_ago = datetime.now() - timedelta(minutes=1)

        if bakchod.history['gamble'] > one_min_ago:
            can_gamble = False
            response = "This is becoming an addiction for you... Come back later!"
            logger.info("/gamble: bakchod.history['gamble'] > one_min_ago")
            return can_gamble, response 
    except:
        logger.info("%s didn't have a history... letting him gamble this time!", bakchod.username)

    try:
        if bakchod.rokda < 50:
            can_gamble = False
            response = "Sorry you need atleast 50 ₹okda to gamble! Come back later..."
            logger.info("/gamble: rokda too low")
            return can_gamble, response 
    except:
        can_gamble = False
        response = "I don't know you yet... come back later!"
        return can_gamble, response

    return can_gamble, response

def get_random_bakchod(group, bakchod_id):

    random_bakchod = bakchod.Bakchod(0, "cr")

    if group is not None:

        members = group.members

        random_index = random.randint(0, len(members)-1)
        random_bakchod_id = members[random_index]
        random_bakchod = bakchod_util.get_bakchod(random_bakchod_id)

        if random_bakchod.id == bakchod_id:
            return bakchod.Bakchod(0, "cr")

    return random_bakchod



