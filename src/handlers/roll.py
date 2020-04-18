from loguru import logger
from util import util, config
from db import dao
import random
import traceback
import datetime
import ciso8601
from models.bakchod import Bakchod
import telegram

chaddi_config = config.get_config()


def handle(update, context):

    util.log_chat("roll", update)

    try:
        command = extract_command_from_update(update)

        if command == "start":

            create_new_roll = False

            group_id = get_group_id_from_update(update)
            if group_id is None:
                update.message.reply_text(text="Roll only be used in a group!")
                return

            current_roll = dao.get_roll_by_id(group_id)
            if current_roll is None:
                create_new_roll = True

            # Handle expired roll
            roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
            if roll_expiry <= datetime.datetime.now():
                create_new_roll = True

            # Allow admins to create new rolls
            if util.is_admin(update.message.from_user["id"]):
                create_new_roll = True

            if create_new_roll:

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
                update.message.reply_text(
                    text=response, parse_mode=telegram.ParseMode.MARKDOWN
                )
                return

            else:
                # Handle when not create_new_roll
                update.message.reply_text("Chal kat re bsdk!")
                return

        elif command == "reset":

            if util.is_admin(update.message.from_user["id"]):

                # Schedule callback for resetting roll effects
                context.job_queue.run_once(
                    reset_roll_effects, 1, context=update.message.chat_id
                )
                return

            else:
                update.message.reply_text("Chal kat re bsdk!")
                return

        else:

            # Return roll status for anything else

            group_id = get_group_id_from_update(update)
            if group_id is None:
                update.message.reply_text(
                    text="Roll can only be used in a group!"
                )
                return

            current_roll = dao.get_roll_by_id(group_id)

            if current_roll is None:
                update.message.reply_text(
                    text="No active roulette right now. `/roll start` to start one!",
                    parse_mode=telegram.ParseMode.MARKDOWN,
                )
                return
            else:
                # Handle expired roll
                roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
                if roll_expiry <= datetime.datetime.now():
                    update.message.reply_text(
                        text="No active roulette right now. `/roll start` to start one!",
                        parse_mode=telegram.ParseMode.MARKDOWN,
                    )
                    return
                else:
                    pretty_roll = generate_pretty_roll(current_roll)
                    response = "* Current active roulette:* {}".format(pretty_roll)
                    update.message.reply_text(
                        text=response, parse_mode=telegram.ParseMode.MARKDOWN
                    )
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

        # Check whether roll already a winrar
        if current_roll["winrar"] is not None:
            logger.info("[roll] current_roll already has a winrar... skipping")
            return

        # Check roll expiry
        roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
        if roll_expiry <= datetime.datetime.now():
            logger.info("[roll] current_roll has expired... skipping")
            return

        # Check and update roll history
        roller = dao.get_bakchod_by_id(update.message.from_user.id)
        history = roller.history
        
        five_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)
        
        if "roll" in history:
            last_time_rolled = ciso8601.parse_datetime(history["roll"])
            if last_time_rolled > five_min_ago:
                logger.info("[roll] rolled too soon... skipping")
                update.message.reply_text(
                    "You can only roll once every 5 mins... Ignoring this roll!"
                )
                return
        else:
            history["roll"] = datetime.datetime.now()
            roller.history = history
            dao.insert_bakchod(roller)

        # Check roll outcome
        roll_number = int(current_roll["roll_number"])

        if dice_value == roll_number:

            # Handle roll winrar
            winrar_bakchod = dao.get_bakchod_by_id(update.message.from_user.id)

            logger.info(
                "[roll] We got a winrar! bakchod={} roll_number={} group_id={}",
                util.extract_pretty_name_from_bakchod(winrar_bakchod),
                roll_number,
                group_id,
            )

            current_roll["winrar"] = winrar_bakchod.id

            # Update roll in DB
            dao.insert_roll(
                current_roll["group_id"],
                current_roll["rule"],
                current_roll["roll_number"],
                current_roll["victim"],
                current_roll["winrar"],
                current_roll["expiry"],
            )

            # Add roll effect to victims modifiers
            victim = dao.get_bakchod_by_id(current_roll["victim"])
            modifiers = victim.modifiers

            if current_roll["rule"] == "mute_user":
                modifiers["censored"] = True

            victim.modifiers = modifiers
            dao.insert_bakchod(victim)

            response = "*WINRAR!!!* {}".format(generate_pretty_roll(current_roll))
            update.message.reply_text(
                text=response, parse_mode=telegram.ParseMode.MARKDOWN
            )

            # Schedule callback for resetting roll effects in 1 hour
            context.job_queue.run_once(
                reset_roll_effects, 3600, context=update.message.chat_id
            )

    except Exception as e:
        logger.error(
            "Caught Error in roll.handle_dice_rolls - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return


def reset_roll_effects(context: telegram.ext.CallbackContext):

    # Get group_id
    group_id = context.job.context

    # Get relevant roll based on group_id
    roll = dao.get_roll_by_id(group_id)

    # Get victim's Bakchod
    victim = dao.get_bakchod_by_id(roll["victim"])

    logger.info(
        "[roll] Resetting roll effects for {} in group={}",
        util.extract_pretty_name_from_bakchod(victim),
        group_id,
    )

    # Reset victim's modifiers
    victim.modifiers = {}

    dao.insert_bakchod(victim)

    # Post reset message
    response = "Roll Modifiers for {} are now removed!".format(
        util.extract_pretty_name_from_bakchod(victim)
    )
    context.bot.send_message(
        group_id, text=response,
    )

    return


def start_new_daily_roll(context: telegram.ext.CallbackContext):

    for group_id in chaddi_config["good_morning_channels"]:

        logger.info("[roll] starting new daily roll! group_id={}", group_id)

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
            context.bot.send_message(
                chat_id=group_id,
                text="bhaaaaaaaaaaaaak",
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

        pretty_roll = generate_pretty_roll(roll)
        response = "*Started new roulette!* " + pretty_roll

        context.bot.send_message(
            chat_id=group_id, text=response, parse_mode=telegram.ParseMode.MARKDOWN,
        )


def generate_pretty_roll(roll):

    pretty_roll = None

    victim = dao.get_bakchod_by_id(roll["victim"])

    try:

        if roll["winrar"] is None:

            pretty_roll = "Roll a {} to `{}` {}!".format(
                roll["roll_number"],
                roll["rule"],
                util.extract_pretty_name_from_bakchod(victim),
            )

        else:

            winrar = dao.get_bakchod_by_id(roll["winrar"])

            roll_expiry = ciso8601.parse_datetime(roll["expiry"])
            now = datetime.datetime.now()
            td = roll_expiry - now

            pretty_roll = "{} won by rolling a {}! {} has now been `{}` for {}".format(
                util.extract_pretty_name_from_bakchod(winrar),
                roll["roll_number"],
                util.extract_pretty_name_from_bakchod(victim),
                roll["rule"],
                util.pretty_time_delta(td.total_seconds()),
            )

    except Exception as e:
        logger.error(
            "Caught Error in roll.generate_pretty_roll - {} \n {}",
            e,
            traceback.format_exc(),
        )

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
        if (
            update.message.chat.id is not None
            and update.message.chat.type == "group"
            or update.message.chat.type == "supergroup"
        ):
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
