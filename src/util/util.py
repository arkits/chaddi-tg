from loguru import logger
from util import config
import json
from datetime import datetime, date, timezone
import random

chaddi_config = config.get_config()

# Read verbLookupTable on startup
verbLookupTable_file = open("resources/verbPastLookup.json", "r")
verbLookupTable = json.loads(verbLookupTable_file.read())


def get_verbLookupTable():
    return verbLookupTable


def print_title():
    print("~~~~ ~~~~ ~~~~ ~~~~")
    print("🙏 ChaddiBot 🙏")
    print("~~~~ ~~~~ ~~~~ ~~~~")


def log_chat(handler_name, update):

    pretty_name = "A Chutiya"

    try:
        if update.message.from_user["username"] is not None:
            pretty_name = update.message.from_user["username"]
        elif update.message.from_user["first_name"] is not None:
            pretty_name = update.message.from_user["first_name"]
        elif update.message.from_user["id"] is not None:
            pretty_name = update.message.from_user["id"]
    except Exception as e:
        pass

    try:
        logger.info(
            "[{}] Handling request from user '{}' in group '{}'",
            handler_name,
            pretty_name,
            update.message.chat.title,
        )
    except Exception as e:
        # This is by design... logging shouldn't throw an Error,
        # only my terrible coding should!
        pass


def is_admin(og_bakchod):

    allowed_setters = chaddi_config["allowed_setters"]

    if str(og_bakchod) in allowed_setters:
        logger.info("[is_admin] og_bakchod={} in config.allowed_setters", og_bakchod)
        return True
    else:
        logger.info(
            "[is_admin] og_bakchod={} not in config.allowed_setters", og_bakchod
        )
        return False


# Generates a human readable time_delta
def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%dd %dh %dm %ds" % (days, hours, minutes, seconds)
    elif hours > 0:
        return "%dh %dm %ds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%dm %ds" % (minutes, seconds)
    else:
        return "%ds" % (seconds,)


def extract_pretty_name_from_bakchod(bakchod):

    pretty_name = "A Chutiya"

    if bakchod.username:
        pretty_name = "@" + bakchod.username
    elif bakchod.first_name:
        pretty_name = bakchod.first_name
    elif bakchod.id:
        pretty_name = bakchod.id

    return pretty_name


def extract_pretty_name_from_tg_user(bakchod):

    pretty_name = "A Chutiya"

    if bakchod["username"]:
        pretty_name = "@" + bakchod["username"]
    elif bakchod["first_name"]:
        pretty_name = bakchod["first_name"]
    elif bakchod["id"]:
        pretty_name = bakchod["id"]

    return pretty_name


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


def choose_random_element_from_list(input_list):

    random.seed(datetime.now())
    random_int = random.randint(0, len(input_list) - 1)

    return input_list[random_int]