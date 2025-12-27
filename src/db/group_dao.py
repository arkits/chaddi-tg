import datetime

from loguru import logger
from peewee import DoesNotExist
from telegram import Chat, Update

from src.db import Bakchod, Group, GroupMember, Message


def get_or_create_group_from_chat(chat: Chat) -> Group:
    try:
        return Group.get(Group.group_id == chat.id)

    except DoesNotExist:
        return Group.create(
            group_id=chat.id,
            name=chat.title,
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
        )


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
        _groupmember = GroupMember.get(
            (GroupMember.group_id == group.group_id) & (GroupMember.bakchod_id == bakchod.tg_id)
        )
    except DoesNotExist:
        _groupmember = GroupMember.create(group=group, bakchod=bakchod)

    # logger.debug("[db] updated Group - id={}", group.name)

    return


def get_group_from_update(update: Update) -> Group:
    try:
        return Group.get(Group.group_id == update.message.chat.id)

    except DoesNotExist:
        return Group.create(
            group_id=update.message.chat.id,
            name=update.message.chat.title,
            created=datetime.datetime.now(),
            updated=datetime.datetime.now(),
        )


def get_group_by_id(group_id: str) -> Group:
    try:
        return Group.get(Group.group_id == group_id)

    except DoesNotExist:
        return None


def get_all_groupmembers_by_group_id(group_id: str):
    groupmembers = GroupMember.select().limit(100).where(GroupMember.group_id == group_id).execute()

    return groupmembers


def get_all_messages_by_group_id(group_id: str, page_number: int, items_per_page: int):
    messages = (
        Message.select()
        .order_by(Message.time_sent.desc())
        .where(Message.to_id == group_id)
        .paginate(page_number, items_per_page)
        .execute()
    )

    return messages


def remove_bakchod_from_group(bakchod: Bakchod, group_id: str):
    try:
        GroupMember.delete().where(
            (GroupMember.group_id == group_id) & (GroupMember.bakchod_id == bakchod.tg_id)
        ).execute()

    except Exception as e:
        logger.warning(
            "[group_dao] Caught Ex remove_bakchod_from_group - bakchod={} group_id={} e={}",
            bakchod,
            group_id,
            e,
        )
