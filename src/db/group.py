from peewee import DoesNotExist
from telegram import Update
from . import Bakchod, Group, GroupMember
from loguru import logger
import datetime


def log_group_from_update(update: Update):

    # logger.debug("[log] Building Group based on update={}", update.to_json())

    try:

        # Check if Group exists
        group = Group.get(Group.group_id == update.message.chat.id)

        # Update Group details
        group.name = update.message.chat.title
        group.updated = datetime.datetime.now()
        group.save()

    except DoesNotExist:

        # Create Group from scratch
        group = Group.create(
            group_id=update.message.chat.id,
            name=update.message.chat.title,
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
        )

    bakchod = Bakchod.get_by_id(update.message.from_user.id)

    try:
        groupmember = GroupMember.get(
            (GroupMember.group_id == group.group_id)
            & (GroupMember.bakchod_id == bakchod.tg_id)
        )
    except DoesNotExist:
        groupmember = GroupMember.create(group=group, bakchod=bakchod)

    logger.debug("[db] updated Group - id={}", group.name)

    return
