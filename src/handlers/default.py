from loguru import logger
from db import dao
from models.bakchod import Bakchod
from models.group import Group
from domain import bakchod as bakchod_domain
import time
import datetime
from handlers import bestie, hi


def all(update, context):

    bakchod = dao.get_bakchod_by_id(update.message.from_user.id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        logger.info("Looks like we have a new Bakchod! - {}", bakchod.__dict__)

    bakchod = update_bakchod(bakchod, update)

    group = dao.get_group_by_id(update.message.chat.id)

    if group is None:
        group = Group.fromUpdate(update)
        logger.info("Looks like we have a new Group! - {}", group.__dict__)

    update_group(group, bakchod, update)

    logger.info(
        "[default.all] b.username='{}' b.rokda={} g.title='{}'",
        bakchod.username,
        bakchod.rokda,
        group.title,
    )

    message_text = update.message.text

    if message_text is not None:

        # Handle 'hi' messages
        if "hi" == message_text.lower():
            hi.handle(update, context)

        # Handle bestie messages
        if "bestie" in message_text.lower():
            bestie.handle(update, context)


def status_update(update, context):

    group = dao.get_group_by_id(update.message.chat.id)

    if group is None:
        group = Group.fromUpdate(update)

    # Handle new_chat_title
    new_chat_title = update.message.new_chat_title

    if new_chat_title is not None:
        group.title = new_chat_title
        logger.info("[status_update] new_chat_title g.title={}", group.title)
        dao.insert_group(group)

    # Handle new_chat_member
    new_chat_members = update.message.new_chat_members

    if new_chat_members is not None:
        for new_member in new_chat_members:
            bakchod = Bakchod(new_member.id, new_member.username, new_member.first_name)
            dao.insert_bakchod(bakchod)

            if bakchod.id not in group.members:
                group.members.append(bakchod.id)
                dao.insert_group(group)

                logger.info(
                    "[status_update] new_chat_member g.title={} b.username={}",
                    group.title,
                    bakchod.username,
                )

    # Handle left_chat_member
    left_chat_member = update.message.left_chat_member

    if left_chat_member is not None:
        group.members.remove(left_chat_member.id)
        dao.insert_group(group)

        logger.info(
            "[status_update] left_chat_member g.title={} b.username={}",
            group.title,
            left_chat_member.username,
        )


def update_bakchod(bakchod, update):

    # usernames and first_name are mutable... have to keep them in sync
    bakchod.username = update.message.from_user.username
    bakchod.first_name = update.message.from_user.first_name

    # Update rokda
    bakchod.rokda = bakchod_domain.reward_rokda(bakchod.rokda)

    # Update lastseen
    bakchod.lastseen = datetime.datetime.now()

    # Persist updated Bakchod
    dao.insert_bakchod(bakchod)

    return bakchod


def update_group(group, bakchod, update):

    # group title is mutable... have to keep in sync
    group.title = update.message.chat.title

    # Add Bakchod to Group
    if bakchod.id not in group.members:
        group.members.append(bakchod.id)

    # Persist updated Group
    dao.insert_group(group)
