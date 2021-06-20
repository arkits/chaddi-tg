import traceback
from loguru import logger
import shortuuid
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from src.domain import config, dc, util
from src.db import Bakchod, Roll, bakchod_dao, group_dao, roll_dao
import random
import datetime
import ciso8601

ROLL_TYPES = ["mute_user", "auto_mom", "kick_user"]
PRETTY_ROLL_MAPPING = {"mute_user": "mute", "auto_mom": "/mom", "kick_user": "kick"}
DEBUG = False

app_config = config.get_config()
BOT_USERNAME = app_config.get("TELEGRAM", "BOT_USERNAME")


def handle(update: Update, context: CallbackContext):

    dc.log_command_usage("roll", update)

    try:

        command = _extract_command_from_update(update)

        if command == "start":

            handle_command_start(update)

        elif command == "reset":

            handle_command_reset(update, context)

        else:

            handle_command_default(update)

    except Exception as e:
        logger.error(
            "Caught Error in roll.handle - {} \n {}",
            e,
            traceback.format_exc(),
        )


def handle_command_default(update: Update):
    """
    Return roll status for anything else
    """

    group_id = _get_group_id_from_update(update)
    if group_id is None:
        update.message.reply_text(text="Roll can only be used in a group!")
        return

    current_roll = roll_dao.get_roll_by_group_id(group_id)

    if current_roll is None:
        update.message.reply_text(
            text="No active roulette right now. <code>/roll start</code> to start one!",
            parse_mode=ParseMode.HTML,
        )
        return
    else:

        if current_roll.expiry <= datetime.datetime.now():

            # Handle expired roll
            update.message.reply_text(
                text="No active roulette right now. <code>/roll start</code> to start one!",
                parse_mode=ParseMode.HTML,
            )
            return

        else:

            pretty_roll_desc = _generate_pretty_roll_description(current_roll)
            response = "<b>Started new roulette!</b> {}".format(pretty_roll_desc)
            update.message.reply_text(text=response, parse_mode=ParseMode.HTML)
            return


def handle_command_start(update: Update):
    create_new_roll = False

    group_id = _get_group_id_from_update(update)
    if group_id is None:
        update.message.reply_text(text="Roll only be used in a group!")
        return

    current_roll = roll_dao.get_roll_by_group_id(group_id)

    if current_roll is None:
        create_new_roll = True
    else:
        # Pre-exisitng roll... check if expired
        if current_roll.expiry <= datetime.datetime.now():
            create_new_roll = True

    # Allow admins to create new rolls
    if util.is_admin_tg_user(update.message.from_user):
        create_new_roll = True

    if create_new_roll:

        roll = generate_new_roll(update, group_id)
        if roll is None:
            update.message.reply_text(text="Couldn't start a new roll :(")
            return

        pretty_roll_desc = _generate_pretty_roll_description(roll)
        response = "<b>Started new roulette!</b> {}".format(pretty_roll_desc)
        update.message.reply_text(text=response, parse_mode=ParseMode.HTML)
        return

    else:
        # Handle when not create_new_roll
        update.message.reply_text("Chal kat re bsdk!")
        return


def handle_command_reset(update: Update, context: CallbackContext):

    if util.is_admin_tg_user(update.message.from_user):

        # Remove schedule reset job
        for job in context.job_queue.jobs():
            if (
                job.name == "reset_roll_effects"
                and job.context == update.message.chat_id
            ):
                logger.info("[roll] Removing pre-scheduled reset_roll_effects job...")
                job.schedule_removal()

        # Schedule callback for resetting roll effects
        context.job_queue.run_once(
            reset_roll_effects, 1, context=update.message.chat_id
        )
        return

    else:
        update.message.reply_text("Chal kat re bsdk!")
        return


def handle_dice_rolls(dice_value, update, context):

    try:

        logger.info("[roll] handle_dice_rolls dice_value={}", dice_value)

        # Extract Group ID
        group_id = _get_group_id_from_update(update)
        if group_id is None:
            logger.info("[roll] dice roll was not in a group... skipping")
            return

        # Get current roll based on group_id
        current_roll = roll_dao.get_roll_by_group_id(group_id)
        if current_roll is None:
            logger.info("[roll] current_roll was a None... skipping")
            return

        # Check whether roll already a winrar
        if current_roll.winrar is not None:
            logger.info("[roll] current_roll already has a winrar... skipping")
            return

        # Check roll expiry
        if current_roll.expiry <= datetime.datetime.now():
            logger.info("[roll] current_roll has expired... skipping")
            return

        # Check and update roll history
        roller = bakchod_dao.get_bakchod_from_update(update)

        if "last_time_rolled" in roller.metadata:

            last_time_rolled = ciso8601.parse_datetime(
                roller.metadata["last_time_rolled"]
            )

            five_min_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)

            if not DEBUG:
                if last_time_rolled > five_min_ago:
                    logger.info("[roll] rolled too soon... skipping")
                    update.message.reply_text(
                        "You can only roll once every 5 mins... Ignoring this roll!"
                    )
                    return
            else:
                logger.debug("[roll] DEBUG is True... ignoring time check")

        roller.metadata["last_time_rolled"] = datetime.datetime.now().isoformat()
        roller.save()

        # Check roll outcome
        roll_number = int(current_roll.goal)

        if dice_value == roll_number:

            logger.info(
                "[roll] We got a winrar! bakchod={} roll_number={} group_id={}",
                util.extract_pretty_name_from_bakchod(roller),
                roll_number,
                group_id,
            )

            current_roll.winrar = roller
            current_roll.expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

            # Update roll in DB
            current_roll.save()

            # Add roll effect to victims modifiers
            victim = current_roll.victim
            victim_metadata = victim.metadata

            if current_roll.rule == "mute_user":

                if "censored" in victim_metadata:
                    censored_modifier = victim_metadata["censored"]
                else:
                    censored_modifier = {}

                if "group_ids" not in censored_modifier:
                    censored_modifier["group_ids"] = []

                censored_modifier["group_ids"].append(group_id)

                victim_metadata["censored"] = censored_modifier

                victim.metadata = victim_metadata
                victim.save()

            elif current_roll.rule == "auto_mom":

                if "auto_mom" in victim_metadata:
                    auto_mom_modifier = victim_metadata["auto_mom"]
                else:
                    auto_mom_modifier = {}

                if "group_ids" not in auto_mom_modifier:
                    auto_mom_modifier["group_ids"] = []

                auto_mom_modifier["group_ids"].append(group_id)

                victim_metadata["auto_mom"] = auto_mom_modifier

                victim.metadata = victim_metadata
                victim.save()

            elif current_roll.rule == "kick_user":

                try:

                    logger.info(
                        "[roll] Kicking User - group_id={} victim.id={}",
                        group_id,
                        util.extract_pretty_name_from_bakchod(victim),
                    )
                    context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text="BYEEEEEEEEEEEE "
                        + util.extract_pretty_name_from_bakchod(victim),
                    )

                    # refer to https://python-telegram-bot.readthedocs.io/en/stable/telegram.bot.html#telegram.Bot.kick_chat_member
                    ban_until = datetime.datetime.now() + datetime.timedelta(seconds=31)
                    context.bot.kick_chat_member(
                        chat_id=group_id, user_id=victim.tg_id, until_date=ban_until
                    )

                    # remove the victim from group members list
                    group_dao.remove_bakchod_from_group(victim, group_id)

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

            response = "<b>WINRAR!!!</b> {}".format(
                _generate_pretty_roll_description(current_roll)
            )
            update.message.reply_text(text=response, parse_mode=ParseMode.HTML)

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


def generate_new_roll(update, group_id):

    # Roll params
    roll_id = shortuuid.uuid()
    created = None
    updated = None
    expiry = None
    rule = None
    roll_group = group_dao.get_group_by_id(group_id)
    victim = None
    goal = None

    params = _extract_params_from_update(update)

    # Build the roll from message params
    if len(params) >= 4:

        param_rule = params[2]
        if param_rule in ROLL_TYPES:
            rule = param_rule

        param_victim_username = params[3]
        victim = bakchod_dao.get_bakchod_by_username(param_victim_username)

        logger.debug("[roll] parsed params rule={} victim={}", rule, victim)

    if rule is None:
        rule = _get_random_roll_type()

    if goal is None:
        goal = random.randint(1, 6)

    if victim is None:
        victim = _get_random_bakchod_from_group(group_id)

    created = datetime.datetime.now()
    updated = datetime.datetime.now()
    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)

    # Check if a roll exists for group
    r = roll_dao.get_roll_by_group_id(group_id)
    if r is None:
        r = Roll.create(
            roll_id=roll_id,
            created=created,
            updated=updated,
            expiry=expiry,
            rule=rule,
            goal=goal,
            group=roll_group,
            victim=victim,
            winrar=None,
        )
    else:
        r.created = created
        r.updated = updated
        r.expiry = expiry
        r.rule = rule
        r.goal = goal
        r.group = roll_group
        r.victim = victim
        r.winrar = None

        r.save()

    logger.debug("[roll] generated roll={}", r.__dict__)

    return r


def _extract_command_from_update(update):

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


def _extract_params_from_update(update):

    params = None

    try:
        # Extract query...
        query = update.message.text
        query = query.lower()
        params = query.split(" ")

    except Exception as e:
        pass

    return params


def _get_group_id_from_update(update) -> str:

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


def _get_random_roll_type() -> str:

    random.seed(datetime.datetime.now())
    random_int = random.randint(0, len(ROLL_TYPES) - 1)

    return ROLL_TYPES[random_int]


def _generate_pretty_roll_description(roll: Roll) -> str:

    pretty_roll = None

    try:

        if roll.winrar is None:

            pretty_roll = "Roll a {} to {} {}!".format(
                roll.goal,
                _pretty_roll_rule(roll.rule),
                util.extract_pretty_name_from_bakchod(roll.victim),
            )

        else:

            now = datetime.datetime.now()
            td = roll.expiry - now

            if roll.rule == "kick_user":
                pretty_roll = "{} won by rolling a {}! {} has been kicked from this group!".format(
                    util.extract_pretty_name_from_bakchod(roll.winrar),
                    roll.goal,
                    util.extract_pretty_name_from_bakchod(roll.victim),
                )
            else:
                pretty_roll = "{} won by rolling a {}! {} is now {} for {}".format(
                    util.extract_pretty_name_from_bakchod(roll.winrar),
                    roll.goal,
                    util.extract_pretty_name_from_bakchod(roll.victim),
                    _pretty_roll_rule(roll.rule),
                    util.pretty_time_delta(td.total_seconds()),
                )

    except Exception as e:
        logger.error(
            "Caught Error in roll.generate_pretty_roll - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return pretty_roll


def _pretty_roll_rule(roll_rule: str) -> str:

    if roll_rule in PRETTY_ROLL_MAPPING.keys():
        return PRETTY_ROLL_MAPPING[roll_rule]
    else:
        return None


def reset_roll_effects(context: CallbackContext):

    # Get group_id
    group_id = context.job.context

    # Get relevant roll based on group_id
    roll = roll_dao.get_roll_by_group_id(group_id)

    victim = roll.victim

    logger.info(
        "[roll] Resetting roll effects for {} in group={}",
        util.extract_pretty_name_from_bakchod(victim),
        group_id,
    )

    # Reset victim's modifiers
    if roll.rule == "mute_user":

        censored_metadata = victim.metadata["censored"]
        if censored_metadata is not None:
            censored_metadata["group_ids"].remove(group_id)
            victim.metadata["censored"] = censored_metadata

            logger.debug("[roll] updated censored_metadata for victim={}", victim)

    elif roll.rule == "auto_mom":

        auto_mom_metadata = victim.metadata["auto_mom"]
        if auto_mom_metadata is not None:
            auto_mom_metadata["group_ids"].remove(group_id)
            victim.metadata["auto_mom"] = auto_mom_metadata

            logger.debug("[roll] updated auto_mom_metadata for victim={}", victim)

    victim.save()

    # Post reset message
    response = "Roll Modifiers for {} are now removed!".format(
        util.extract_pretty_name_from_bakchod(victim)
    )
    context.bot.send_message(
        group_id,
        text=response,
    )

    return


def _get_random_bakchod_from_group(group_id: str) -> Bakchod:

    all_groupmembers = group_dao.get_all_groupmembers_by_group_id(group_id=group_id)

    random_groupmember = util.choose_random_element_from_list(all_groupmembers)

    keep_searching = True

    while keep_searching:

        if random_groupmember.bakchod.username != BOT_USERNAME:
            keep_searching = False
        else:
            logger.debug("[roll] random_bakchod returned Bot... trying again")
            keep_searching = False
            random_groupmember = util.choose_random_element_from_list(all_groupmembers)

    return random_groupmember.bakchod
