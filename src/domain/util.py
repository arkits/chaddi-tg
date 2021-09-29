from loguru import logger
from telegram import update
from telegram.user import User
import os
import random
from datetime import datetime
from src.db import Bakchod, GroupMember
import en_core_web_sm
from . import config
import json


app_config = config.get_config()

ADMIN_IDS = app_config.get("TELEGRAM", "TG_ADMIN_USERS")

# Load Spacy English Language Pack
nlp = en_core_web_sm.load()


ROKDA_STRING = "₹okda"


# Read verbLookupTable on startup
verb_past_lookup_file = open("resources/verb-past-lookup.json", "r")
verb_past_lookup = json.loads(verb_past_lookup_file.read())


def get_verb_past_lookup():
    return verb_past_lookup


def get_nlp():
    return nlp


def extract_pretty_name_from_tg_user(user: User) -> str:
    if user.username is not None:
        return "@" + user.username
    elif user.first_name is not None:
        return user.first_name
    elif user.full_name is not None:
        return user.full_name
    elif user.id:
        return str(user.id)


def extract_pretty_name_from_bakchod(bakchod: Bakchod) -> str:
    if bakchod.username:
        return "@" + bakchod.username
    elif bakchod.pretty_name:
        return bakchod.pretty_name
    elif bakchod.tg_id:
        return str(bakchod.tg_id)
    else:
        return None


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)
        logger.info("[util] deleted file! file={}", file)
    else:
        logger.warning("[util] unabled to delete... does not exist file={}", file)


def choose_random_element_from_list(input_list):
    random.seed(datetime.now())
    random_int = random.randint(0, len(input_list) - 1)
    return input_list[random_int]


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


def get_random_bakchod_from_group(group_id: str, bakchod_id_to_avoid: str) -> Bakchod:

    groupmembers = (
        GroupMember.select().where(GroupMember.group_id == group_id).execute()
    )

    random_groupmember = choose_random_element_from_list(groupmembers)

    random_bakchod = Bakchod.get_by_id(random_groupmember.bakchod_id)
    logger.info("random_bakchod={}", random_bakchod.username)

    return random_bakchod


def is_admin_tg_user(user: User):
    if str(user.id) in ADMIN_IDS:
        return True
    else:
        return False


def paywall_user(bakchod_id: str, cost):

    b = Bakchod.get_by_id(bakchod_id)

    if b is not None:
        if b.rokda <= cost:
            logger.info("[paywall] {} doesn't have enough rokda cost={}", b.tg_id, cost)
            return False
        else:
            b.rokda = b.rokda - cost
            b.save()
            return True
    else:
        return False


def get_group_id_from_update(update: update):

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