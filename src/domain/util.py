from loguru import logger
from telegram import Update
from telegram.user import User


def extract_pretty_name_from_tg_user(user: User) -> str:
    if user.username:
        return "@" + user.username
    elif user.first_name:
        return user.first_name
    elif user.id:
        return str(user.id)
