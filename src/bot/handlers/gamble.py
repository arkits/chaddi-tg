import traceback
from loguru import logger
from telegram import Update
from src.db import Bakchod, bakchod_dao
from src.domain import dc, util
import datetime
import random
import ciso8601


def handle(update: Update, context):

    try:

        dc.log_command_usage("gamble", update)

        b = bakchod_dao.get_or_create_bakchod_from_tg_user(update.message.from_user)

        can_gamble, response = can_bakchod_gamble(b)
        if not can_gamble:
            update.message.reply_text(response)
            return

        response = gamble(b, update)
        update.message.reply_text(response)

    except Exception as e:
        logger.error(
            "Caught Error in gamble.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


def gamble(bakchod: Bakchod, update: Update):

    response = None

    random_bakchod = util.get_random_bakchod_from_group(
        str(update.message.chat.id), bakchod.tg_id
    )

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

    random_bakchod.save()

    # Update metadata
    bakchod.metadata["last_time_gambled"] = datetime.datetime.now().isoformat()
    bakchod.save()

    logger.info(
        "[gamble] {} gambled - response='{}'",
        util.extract_pretty_name_from_bakchod(bakchod),
        response,
    )

    return response


def can_bakchod_gamble(bakchod: Bakchod):

    can_gamble = True
    response = None

    if "last_time_gambled" in bakchod.metadata:

        last_time_gambled = ciso8601.parse_datetime(
            bakchod.metadata["last_time_gambled"]
        )

        logger.info("[gamble] metadata['last_time_gambled']={}", last_time_gambled)

    else:
        logger.info("[gamble] metadata['last_time_gambled'] was not there")
        can_gamble = True
        return can_gamble, response

    one_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)

    if last_time_gambled > one_min_ago:
        can_gamble = False
        response = "This is becoming an addiction for you... Come back later!"
        logger.info("[gamble] metadata['last_time_gambled'] > one_min_ago")
        return can_gamble, response

    if bakchod.rokda < 50:
        can_gamble = False
        response = "Sorry you need atleast 50 ₹okda to gamble! Come back later..."
        logger.info("[gamble] rokda too low")
        return can_gamble, response

    return can_gamble, response
