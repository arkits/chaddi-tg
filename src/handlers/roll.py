from loguru import logger
from util import util, config
from db import dao
import random
import traceback
import datetime
import ciso8601
from models.bakchod import Bakchod
import telegram
import math

chaddi_config = config.get_config()

ROLL_TYPES = ["mute_user", "auto_mom", "kick_user"]
PRETTY_ROLL_MAPPING = {"mute_user": "mute", "auto_mom": "/mom", "kick_user": "kick"}
DEBUG = False


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
            else:
                # Pre-exisitng roll... check if expired
                roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
                if roll_expiry <= datetime.datetime.now():
                    create_new_roll = True

            # Allow admins to create new rolls
            if util.is_admin(update.message.from_user["id"]):
                create_new_roll = True

            if create_new_roll:

                # Create new roll...

                # Set roll rule type
                rule = get_random_roll_type()

                # Set the number to required to win
                roll_number = random.randint(1, 6)

                # Extract victim from command param...
                victim = None
                parsed_victim_username = extract_param_from_update(update)
                if parsed_victim_username is not None:
                    victim = dao.get_bakchod_by_username(parsed_victim_username)
                    if victim is not None:
                        logger.info(
                            "[roll] Found passed Bakchod username={} in DB",
                            parsed_victim_username,
                        )

                # Or else get a Random Bakchod
                if victim is None:
                    victim = get_random_bakchod(group_id)

                if victim is None:
                    update.message.reply_text(text="Couldn't get a random Bakchod :(")
                    return

                # Set the roll winrar to None
                winrar = None

                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

                dao.insert_roll(group_id, rule, roll_number, victim.id, winrar, expiry)

                roll = dao.get_roll_by_id(group_id)
                if roll is None:
                    update.message.reply_text(text="Couldn't start a new roll :(")
                    return

                pretty_roll = generate_pretty_roll(roll)
                response = "<b>Started new roulette!</b> " + pretty_roll
                update.message.reply_text(
                    text=response, parse_mode=telegram.ParseMode.HTML
                )
                return

            else:
                # Handle when not create_new_roll
                update.message.reply_text("Chal kat re bsdk!")
                return

        elif command == "reset":

            if util.is_admin(update.message.from_user["id"]):

                # Remove schedule reset job
                for job in context.job_queue.jobs():
                    if (
                        job.name == "reset_roll_effects"
                        and job.context == update.message.chat_id
                    ):
                        logger.info(
                            "[roll] Removing pre-scheduled reset_roll_effects job..."
                        )
                        job.schedule_removal()

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
                update.message.reply_text(text="Roll can only be used in a group!")
                return

            current_roll = dao.get_roll_by_id(group_id)

            if current_roll is None:
                update.message.reply_text(
                    text="No active roulette right now. <code>/roll start</code> to start one!",
                    parse_mode=telegram.ParseMode.HTML,
                )
                return
            else:
                # Handle expired roll
                roll_expiry = ciso8601.parse_datetime(current_roll["expiry"])
                if roll_expiry <= datetime.datetime.now():
                    update.message.reply_text(
                        text="No active roulette right now. <code>/roll start</code> to start one!",
                        parse_mode=telegram.ParseMode.HTML,
                    )
                    return
                else:
                    pretty_roll = generate_pretty_roll(current_roll)
                    response = "<b>Current active roulette:</b> {}".format(pretty_roll)
                    update.message.reply_text(
                        text=response, parse_mode=telegram.ParseMode.HTML
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

        if history is None:
            history = {}

        five_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)

        if not DEBUG:
            if "roll" in history:
                last_time_rolled = ciso8601.parse_datetime(history["roll"])
                if last_time_rolled > five_min_ago:
                    logger.info("[roll] rolled too soon... skipping")
                    update.message.reply_text(
                        "You can only roll once every 5 mins... Ignoring this roll!"
                    )
                    return
        else:
            logger.debug("[roll] DEBUG is True... ignoring time check")

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
            current_roll["expiry"] = datetime.datetime.now() + datetime.timedelta(
                hours=1
            )

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

                if "censored" in modifiers:
                    censored_modifier = modifiers["censored"]
                else:
                    censored_modifier = {}

                if "group_ids" not in censored_modifier:
                    censored_modifier["group_ids"] = []

                censored_modifier["group_ids"].append(group_id)

                modifiers["censored"] = censored_modifier

            elif current_roll["rule"] == "auto_mom":

                if "auto_mom" in modifiers:
                    auto_mom_modifier = modifiers["auto_mom"]
                else:
                    auto_mom_modifier = {}

                if "group_ids" not in auto_mom_modifier:
                    auto_mom_modifier["group_ids"] = []

                auto_mom_modifier["group_ids"].append(group_id)

                modifiers["auto_mom"] = auto_mom_modifier

            elif current_roll["rule"] == "kick_user":

                try:

                    logger.info(
                        "[roll] Kicking User - group_id={} victim.id={}",
                        group_id,
                        victim.id,
                    )
                    context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text="BYEEEEEEEEEEEE "
                        + util.extract_pretty_name_from_bakchod(victim),
                    )
                    context.bot.kick_chat_member(group_id, victim.id)

                except Exception as e:
                    logger.error(
                        "[roll] Caught Error in kick Bakchod - {} \n {}",
                        e,
                        traceback.format_exc(),
                    )
                    context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text="Looks like I'm not able to kick user... Please check the Group permissions!",
                    )
                    return

            victim.modifiers = modifiers
            dao.insert_bakchod(victim)

            response = "<b>WINRAR!!!</b> {}".format(generate_pretty_roll(current_roll))
            update.message.reply_text(text=response, parse_mode=telegram.ParseMode.HTML)

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
    if roll["rule"] == "mute_user":
        censored_modifiers = victim.modifiers["censored"]
        if censored_modifiers is not None:
            censored_modifiers["group_ids"].remove(group_id)
            victim.modifiers["censored"] = censored_modifiers

    elif roll["rule"] == "auto_mom":
        auto_mom_modifiers = victim.modifiers["auto_mom"]
        if auto_mom_modifiers is not None:
            auto_mom_modifiers["group_ids"].remove(group_id)
            victim.modifiers["auto_mom"] = auto_mom_modifiers

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

        # Set roll rule type
        rule = get_random_roll_type()

        # Set the number to required to win
        roll_number = random.randint(1, 6)

        victim = get_random_bakchod(group_id)
        if victim is None:
            context.bot.send_message(
                chat_id=group_id, text="Couldn't get a random Bakchod :("
            )
            return

        winrar = None

        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

        dao.insert_roll(group_id, rule, roll_number, victim.id, winrar, expiry)

        roll = dao.get_roll_by_id(group_id)

        if roll is None:
            context.bot.send_message(
                chat_id=group_id,
                text="bhaaaaaaaaaaaaak",
                parse_mode=telegram.ParseMode.HTML,
            )

        pretty_roll = generate_pretty_roll(roll)
        response = "<b>Started new roulette!</b> " + pretty_roll

        context.bot.send_message(
            chat_id=group_id, text=response, parse_mode=telegram.ParseMode.HTML,
        )


def generate_pretty_roll(roll):

    pretty_roll = None

    victim = dao.get_bakchod_by_id(roll["victim"])

    try:

        if roll["winrar"] is None:

            pretty_roll = "Roll a {} to {} {}!".format(
                roll["roll_number"],
                pretty_roll_rule(roll["rule"]),
                util.extract_pretty_name_from_bakchod(victim),
            )

        else:

            winrar = dao.get_bakchod_by_id(roll["winrar"])

            try:
                roll_expiry = ciso8601.parse_datetime(roll["expiry"])
            except Exception as e:
                roll_expiry = roll["expiry"]

            now = datetime.datetime.now()
            td = roll_expiry - now

            if roll["rule"] == "kick_user":
                pretty_roll = "{} won by rolling a {}! {} has been kicked from this group!".format(
                    util.extract_pretty_name_from_bakchod(winrar),
                    roll["roll_number"],
                    util.extract_pretty_name_from_bakchod(victim),
                )
            else:
                pretty_roll = "{} won by rolling a {}! {} is now {} for {}".format(
                    util.extract_pretty_name_from_bakchod(winrar),
                    roll["roll_number"],
                    util.extract_pretty_name_from_bakchod(victim),
                    pretty_roll_rule(roll["rule"]),
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


def extract_param_from_update(update):

    param = None

    try:
        # Extract query...
        query = update.message.text
        query = query.lower()
        query = query.split(" ")

        try:
            param = query[2:]
            param = "".join(param)

            if param[0] == "@":
                param = param[1:]

        except:
            param = None

    except Exception as e:
        pass

    return param


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

        collected_bakchods = []

        # loop through the member ids and store the bakchod objects
        for member_id in group.members:

            bakchod = dao.get_bakchod_by_id(member_id)

            if bakchod is not None:

                if bakchod.lastseen is not None:

                    try:
                        bakchod.lastseen = ciso8601.parse_datetime(bakchod.lastseen)
                        collected_bakchods.append(bakchod)
                    except Exception as e:
                        logger.error(
                            "Caught Error in roll.get_random_bakchod - {} \n {}",
                            e,
                            traceback.format_exc(),
                        )

        # sort the bakchods by lastseen
        collected_bakchods.sort(key=lambda r: r.lastseen)

        # only care about the x% of the lastseen
        relevant_section = math.ceil(0.15 * len(collected_bakchods))

        # pick a random bakchod from the relevant section
        index = random.randint(0, relevant_section)

        random_bakchod = collected_bakchods[index]

    return random_bakchod


def pretty_roll_rule(roll_rule):

    if roll_rule in PRETTY_ROLL_MAPPING.keys():
        return PRETTY_ROLL_MAPPING[roll_rule]
    else:
        return None


def get_random_roll_type():

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(ROLL_TYPES) - 1)

    return ROLL_TYPES[random_int]
