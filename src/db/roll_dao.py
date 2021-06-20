from peewee import DoesNotExist
from telegram import Update
from loguru import logger
from src.db import Roll, Group


def get_roll_by_group_id(group_id: str) -> Roll:

    try:

        g = Group.get(Group.group_id == group_id)

        return Roll.get(Roll.group == g)

    except DoesNotExist:

        return None