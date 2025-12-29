import datetime

from loguru import logger
from peewee import DoesNotExist
from telegram import Update, User

from src.domain import util

from . import Bakchod


def _create_bakchod(tg_id: int, username: str, pretty_name: str) -> Bakchod:
    return Bakchod.create(
        tg_id=tg_id,
        username=username,
        pretty_name=pretty_name,
        lastseen=datetime.datetime.now(),
        created=datetime.datetime.now(),
        updated=datetime.datetime.now(),
    )


def _get_or_create_bakchod(tg_id: int, username: str, pretty_name: str) -> Bakchod:
    try:
        exists_in_db = Bakchod.get(Bakchod.tg_id == tg_id)
        if exists_in_db is not None:
            return exists_in_db

    except DoesNotExist:
        logger.info("[db] tg_id={} DoesNotExist... Creating new!", tg_id)
        return _create_bakchod(tg_id, username, pretty_name)


def get_bakchod_from_update(update: Update) -> Bakchod:
    tg_id = update.message.from_user.id
    username = update.message.from_user.username
    pretty_name = util.extract_pretty_name_from_tg_user(update.message.from_user)

    return _get_or_create_bakchod(tg_id, username, pretty_name)


def get_or_create_bakchod_from_tg_user(user: User) -> Bakchod:
    tg_id = user.id
    username = user.username
    pretty_name = util.extract_pretty_name_from_tg_user(user)

    return _get_or_create_bakchod(tg_id, username, pretty_name)


def get_bakchod_by_username(username: str) -> Bakchod:
    try:
        exists_in_db = Bakchod.get(Bakchod.username == username)

        if exists_in_db is not None:
            return exists_in_db

    except DoesNotExist:
        logger.warning("[db] username={} DoesNotExist", username)

        return None
