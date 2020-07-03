from loguru import logger
from util import util
from db import dao
from models.bakchod import Bakchod
from domain import metrics

import ciso8601

import datetime
import random


def handle(update, context):

    util.log_chat("gamble", update)

    metrics.inc_gamble_count(update)

    response = gamble(update.message.from_user["id"], update.message.chat["id"], update)

    update.message.reply_text(response)


def gamble(bakchod_id, chat_id, update):

    bakchod = dao.get_bakchod_by_id(bakchod_id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        dao.insert_bakchod(bakchod)

    can_gamble, response = can_bakchod_gamble(bakchod)

    if can_gamble:

        # Get a random_bakchod from the same Group
        group = dao.get_group_by_id(chat_id)
        random_bakchod = get_random_bakchod(group, bakchod_id)

        response, bakchod, random_bakchod = gamble_engine(bakchod, random_bakchod)

        # Update History
        try:
            history = bakchod.history
        except:
            history = {}

        history["gamble"] = datetime.datetime.now()
        bakchod.history = history

        # Update gambler bakchod
        dao.insert_bakchod(bakchod)

        # Update random_bakchod
        if random_bakchod.id != 0:
            dao.insert_bakchod(random_bakchod)

    return response


def gamble_engine(bakchod, random_bakchod):

    response = ""

    roll = random.random()

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
            random_bakchod.username
        )
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
            random_bakchod.username
        )
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
            random_bakchod.username
        )
        bakchod.rokda = bakchod.rokda - 500
        random_bakchod.rokda += 500
    elif roll > 0.01:
        response = "CBI Raided ChaddiInc... That 1000 you just won was derokdatized!"
        bakchod.rokda = bakchod.rokda - 1000
    elif roll > 0.001:
        response = "You lost your entire fortune (and Paul's Kwid) to {}. Gambling can suck!".format(
            random_bakchod.username
        )
        random_bakchod.rokda += bakchod.rokda
        bakchod.rokda = 1

    # Close their accounts at 0 if they're in negatives
    if bakchod.rokda < 0:
        bakchod.rokda = 0
        response = (
            response + " You're bankrupt with 0 ₹okda, enroll into ChaddiInc Narega!"
        )

    return response, bakchod, random_bakchod


def can_bakchod_gamble(bakchod):

    can_gamble = True
    response = None

    try:
        one_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)

        last_time_gambled = ciso8601.parse_datetime(bakchod.history["gamble"])

        if last_time_gambled > one_min_ago:
            can_gamble = False
            response = "This is becoming an addiction for you... Come back later!"
            logger.info("[gamble] bakchod.history['gamble'] > one_min_ago")
            return can_gamble, response
    except Exception as e:
        logger.error("Caught Exception in can_bakchod_gamble - {}", e)

    try:
        if bakchod.rokda < 50:
            can_gamble = False
            response = "Sorry you need atleast 50 ₹okda to gamble! Come back later..."
            logger.info("[gamble] rokda too low")
            return can_gamble, response
    except:
        can_gamble = False
        response = "I don't know you yet... come back later!"
        return can_gamble, response

    return can_gamble, response


def get_random_bakchod(group, bakchod_id):

    if group is not None:

        members = group.members

        random_index = random.randint(0, len(members) - 1)
        random_bakchod_id = members[random_index]
        random_bakchod = dao.get_bakchod_by_id(random_bakchod_id)

        if random_bakchod.id == str(bakchod_id):
            return Bakchod(0, "cr", "cr")

    return random_bakchod
