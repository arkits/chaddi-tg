from loguru import logger
from telegram import Update
from telegram.user import User
import os
import random
from datetime import datetime

from db import Bakchod


def extract_pretty_name_from_tg_user(user: User) -> str:

    if user.first_name is not None:
        return user.first_name
    elif user.full_name is not None:
        return user.full_name
    elif user.username is not None:
        return "@" + user.username
    elif user.id:
        return str(user.id)


def extract_pretty_name_from_bakchod(bakchod: Bakchod) -> str:
    if bakchod.username:
        return "@" + bakchod.username
    elif bakchod.pretty_name:
        return bakchod.pretty_name
    elif bakchod.tg_id:
        return str(bakchod.tg_id)


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)
        logger.info("[util] deleted file! - {}", file)
    else:
        logger.warn("[util] file does not exist - {}", file)


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