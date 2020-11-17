from loguru import logger
from util import config
import json
from datetime import datetime, date, timezone, timedelta
import random
import en_core_web_sm
from db import dao
import ciso8601
import os

chaddi_config = config.get_config()

# Read verbLookupTable on startup
verbLookupTable_file = open("resources/verbPastLookup.json", "r")
verbLookupTable = json.loads(verbLookupTable_file.read())

# Load Spacy English Language Pack
nlp = en_core_web_sm.load()


def get_verbLookupTable():
    return verbLookupTable


def get_nlp():
    return nlp


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


def paywall_user(tg_id, cost):

    bakchod = dao.get_bakchod_by_id(tg_id)

    if bakchod is not None:
        if bakchod.rokda <= cost:
            logger.info(
                "[paywall] {} doesn't have enough rokda cost={}", bakchod.id, cost
            )
            return False
        else:
            bakchod.rokda = bakchod.rokda - cost
            dao.insert_bakchod(bakchod)
            return True
    else:
        return False


def ratelimit_user(update, ratelimit_key, fail_message, timeout_mins):

    limited = False

    # Enforce rate limiting on getting random quotes
    bakchod = dao.get_bakchod_by_id(update.message.from_user.id)
    history = bakchod.history

    if history is None:
        history = {}

    timeout_time = datetime.now() - timedelta(minutes=timeout_mins)

    if ratelimit_key in history:
        last_time_get = ciso8601.parse_datetime(history[ratelimit_key])
        if last_time_get > timeout_time:
            logger.info("[ratelimit] blocked for key={}", ratelimit_key)
            update.message.reply_text(fail_message)
            limited = True
            return limited

    history[ratelimit_key] = datetime.now()
    bakchod.history = history
    dao.insert_bakchod(bakchod)

    return limited


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)
        logger.info("[util] deleted file! - {}", file)
    else:
        logger.warn("[util] file does not exist - {}", file)
