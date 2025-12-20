import json
import os
import random
from datetime import datetime

import en_core_web_sm
import pytz
import requests
from loguru import logger
from telegram import Update, User

from src.db import Bakchod, GroupMember

from . import config

app_config = config.get_config()

ADMIN_IDS = app_config.get("TELEGRAM", "TG_ADMIN_USERS")

# Load Spacy English Language Pack
nlp = en_core_web_sm.load()

ROKDA_STRING = "₹okda"
RESOURCES_DIR = "resources/"

IST_TIMEZONE = pytz.timezone("Asia/Kolkata")
UTC_TIMEZONE = pytz.timezone("UTC")

# Read verbLookupTable on startup
verb_past_lookup_file = open("resources/verb-past-lookup.json")
verb_past_lookup = json.loads(verb_past_lookup_file.read())


def pretty_print_rokda(r):
    return f"{round(r, 2):,}"


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


def acquire_external_resource(resource_url, resource_name):
    resource_path = os.path.join(RESOURCES_DIR, "external", resource_name)

    if os.path.exists(resource_path):
        logger.info(
            "[acquire_external_resource] resource already exist. not dowloading - resource_path={}",
            resource_path,
        )

    else:
        logger.info(
            "[acquire_external_resource] downloading resource_url={}", resource_url
        )

        r = requests.get(resource_url, allow_redirects=True, timeout=30)
        r.raise_for_status()  # Raise an exception for bad status codes

        # Ensure the directory exists
        os.makedirs(os.path.dirname(resource_path), exist_ok=True)

        with open(resource_path, "wb") as f:
            f.write(r.content)

        logger.info(
            "[acquire_external_resource] successfully downloaded resource_path={} size={} bytes",
            resource_path,
            len(r.content),
        )

    return resource_path


def choose_random_element_from_list(input_list):
    try:
        random.seed()
        random_int = random.randint(0, len(input_list) - 1)
        return input_list[random_int]
    except Exception as e:
        logger.warning("Unable to seed random generator: {}", e)
        return input_list[0]


def pretty_time_delta(seconds):
    seconds = int(seconds)
    years, seconds = divmod(seconds, 31536000)  # 365 days
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if years > 0:
        return "%dy %dd %dh %dm %ds" % (years, days, hours, minutes, seconds)
    elif days > 0:
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

    if random_groupmember is None:
        logger.warning("No group members found for group_id={}", group_id)
        return None

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


def get_group_id_from_update(update: Update):
    group_id = None

    try:
        if (
            update.message.chat.id is not None and update.message.chat.type == "group"
        ) or update.message.chat.type == "supergroup":
            group_id = update.message.chat.id
    except Exception:
        pass

    return group_id


def normalize_datetime(dt: datetime):
    if dt.tzinfo is None:
        dt = UTC_TIMEZONE.localize(dt)

    return IST_TIMEZONE.normalize(dt)


def extract_magic_word(target_message):
    doc = get_nlp()(target_message)

    # the types on pos that we care about - refer to https://universaldependencies.org/docs/u/pos/
    accepted_pos_types = ["VERB", "NOUN", "PROPN", "ADJ", "ADV"]

    # Create a dict for storing the tokens sorted by pos types
    tokens_sorted = {}
    for pos_type in accepted_pos_types:
        tokens_sorted[pos_type] = []

    for token in doc:
        for pos_type in accepted_pos_types:
            # logger.debug("token={} - pos={}", token, token.pos_)

            if token.pos_ == pos_type:
                if pos_type == "VERB":
                    tokens_sorted[pos_type].append(token.lemma_)
                else:
                    tokens_sorted[pos_type].append(token.text)

    # remove the key from the dict if it's empty
    # need to use list(), or else python will complain
    for sorted_key in list(tokens_sorted.keys()):
        if len(tokens_sorted[sorted_key]) == 0:
            tokens_sorted.pop(sorted_key, None)

    logger.debug("[extract_magic_word] tokens_sorted={}", tokens_sorted)

    if len(tokens_sorted.keys()) == 0:
        logger.info("[extract_magic_word] tokens_sorted.keys() was zero!")
        return None

    # choose which pos_type to use...
    magic_pos_type = list(tokens_sorted.keys())[0]
    logger.debug("[extract_magic_word] magic_pos_type={}", magic_pos_type)

    # choose magic word...
    magic_word = choose_random_element_from_list(tokens_sorted[magic_pos_type])

    return magic_word
