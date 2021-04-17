from loguru import logger
from telegram import Update
from telegram.user import User

from db import Bakchod


def extract_pretty_name_from_tg_user(user: User) -> str:
    if user.username:
        return "@" + user.username
    elif user.first_name:
        return user.first_name
    elif user.id:
        return str(user.id)


def extract_pretty_name_from_bakchod(bakchod: Bakchod) -> str:
    if bakchod.username:
        return "@" + bakchod.username
    elif bakchod.pretty_name:
        return bakchod.pretty_name
    elif bakchod.tg_id:
        return str(bakchod.tg_id)
