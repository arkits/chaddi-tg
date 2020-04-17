from loguru import logger
from util import util
from telegram import ParseMode
from db import dao
import random
import traceback
import datetime
import ciso8601


def handle(update, context):

    util.log_chat("roll", update)

    try:
        command = extract_command_from_update(update)

        if command == "status":

            group_id = get_group_id_from_update(update)

            if group_id is None:
                update.message.reply_text(
                    text="You can roll can only be used in a group!"
                )
                return

            current_roll = dao.get_roll_by_id(group_id)

            if current_roll is None:
                update.message.reply_text(
                    text="No active roulette right now. `/roll start` to start one!",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            else:
                pretty_roll = generate_pretty_roll(current_roll)
                response = "* Current active roulette - * {}".format(pretty_roll)
                logger.info(response)
                update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)
                return

        elif command == "start":

            group_id = get_group_id_from_update(update)
            if group_id is None:
                update.message.reply_text(
                    text="You can roll can only be used in a group!"
                )
                return

            rule = "mute_user"

            roll_number = random.randint(1, 6)

            victim = get_random_bakchod(group_id)
            if victim is None:
                update.message.reply_text(text="Couldn't get a random Bakchod :(")
                return

            winrar = None

            expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

            dao.insert_roll(group_id, rule, roll_number, victim.id, winrar, expiry)

            roll = dao.get_roll_by_id(group_id)
            if roll is None:
                update.message.reply_text(text="Couldn't start a new roll :(")
                return

            pretty_roll = generate_pretty_roll(roll)
            response = "*Started new roulette!* " + pretty_roll
            update.message.reply_text(text=response, parse_mode=ParseMode.MARKDOWN)

            return

    except Exception as e:
        logger.error(
            "Caught Error in roll.handle - {} \n {}", e, traceback.format_exc(),
        )


def handle_dice_rolls(dice_value, update, context):

    try:

        logger.info("[roll] handle_dice_rolls dice_value={}", dice_value)

        # Extract Group ID
        group_id = get_group_id_from_update(update)
        if group_id is None:
            logger.info("[roll] dice roll was not in a group... skipping")
            return

        # Get current roll based on group_id
        current_roll = dao.get_roll_by_id(group_id)
        if current_roll is None:
            logger.info("[roll] current_roll was a None... skipping")
            return

        # Check roll expiry
        roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
        if roll_expiry <= datetime.datetime.now():
            logger.info("[roll] current_roll has expired... skipping")
            return

        # Check roll outcome
        roll_number = int(current_roll["roll_number"])
        if dice_value == roll_number:
            logger.info("We got a winrar!")
            update.message.reply_text("WINRAR!!!!")
        

    except Exception as e:
        logger.error(
            "Caught Error in roll.handle_dice_rolls - {} \n {}", e, traceback.format_exc(),
        )

    return


def generate_pretty_roll(roll):

    pretty_roll = None

    victim = dao.get_bakchod_by_id(roll["victim"])

    try:
        pretty_roll = "Roll a {} to `{}` {}!".format(
            roll["roll_number"],
            roll["rule"],
            util.extract_pretty_name_from_bakchod(victim),
        )
    except Exception as e:
        pass

    return pretty_roll


def extract_command_from_update(update):

    command = None

    try:
        # Extract query...
        query = update.message.text
        query = query.lower()
        query = query.split(" ")

        try:
            command = query[1]
        except:
            command = "status"

    except Exception as e:
        pass

    return command


def get_group_id_from_update(update):

    group_id = None

    try:
        if update.message.chat.id is not None and update.message.chat.type == "group":
            group_id = update.message.chat.id
    except Exception as e:
        pass

    return group_id


def get_random_bakchod(group_id):

    random_bakchod = None

    group = dao.get_group_by_id(group_id)

    if group is not None:

        members = group.members

        random_index = random.randint(0, len(members) - 1)
        random_bakchod_id = members[random_index]
        random_bakchod = dao.get_bakchod_by_id(random_bakchod_id)

    return random_bakchod
