from peewee import DoesNotExist
from telegram import Update, User
from . import Bakchod
from loguru import logger
import datetime
from domain import util


def get_bakchod_from_update(update: Update) -> Bakchod:

    tg_id = update.message.from_user.id
    username = update.message.from_user.username
    pretty_name = util.extract_pretty_name_from_tg_user(update.message.from_user)

    try:

        exists_in_db = Bakchod.get(Bakchod.tg_id == tg_id)
        # logger.debug("[db] tg_id={} exists_in_db={}", tg_id, exists_in_db)

        if exists_in_db is not None:
            return exists_in_db

    except DoesNotExist:

        logger.info("[db] tg_id={} DoesNotExist", tg_id)

        return Bakchod.create(
            tg_id=tg_id,
            username=username,
            pretty_name=pretty_name,
            lastseen=datetime.datetime.now(),
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
        )


def get_or_create_bakchod_from_tg_user(user: User) -> Bakchod:

    tg_id = user.id
    username = user.username
    pretty_name = util.extract_pretty_name_from_tg_user(user)

    try:

        exists_in_db = Bakchod.get(Bakchod.tg_id == tg_id)
        # logger.debug("[db] tg_id={} exists_in_db={}", tg_id, exists_in_db)

        if exists_in_db is not None:
            return exists_in_db

    except DoesNotExist:

        logger.info("[db] tg_id={} DoesNotExist", tg_id)

        return Bakchod.create(
            tg_id=tg_id,
            username=username,
            pretty_name=pretty_name,
            lastseen=datetime.datetime.now(),
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
        )