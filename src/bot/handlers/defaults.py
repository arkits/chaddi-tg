from datetime import datetime
from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.ext import CallbackContext
from domain import dc
from db import Group, GroupMember, bakchod, group
from . import hi, bestie


def all(update: Update, context: CallbackContext) -> None:
    dc.sync_persistence_data(update)

    # Reward rokda to Bakchod
    b = bakchod.get_bakchod_from_update(update)
    b.rokda = reward_rokda(b.rokda)
    b.updated = datetime.now()
    b.save()


def handle_message_matching(update, context):

    message_text = update.message.text

    if message_text is not None:

        # Handle 'hi' messages
        if "hi" == message_text.lower():
            hi.handle(update, context)

        # Handle bestie messages
        if "bestie" in message_text.lower():
            bestie.handle(update, context)

    return


def reward_rokda(r: int):

    if (r < 0) or r is None:
        r = 0

    # Egalitarian policy - Poor users get more increment than richer users
    r += 100 / (r + 10) + 1
    r = round(r, 2)

    return r


def status_update(update: Update, context: CallbackContext) -> None:

    g = group.get_group_from_update(update)

    # Handle new_chat_member
    new_chat_members = update.message.new_chat_members

    if new_chat_members is not None:
        for new_member in new_chat_members:

            b = bakchod.get_or_create_bakchod_from_tg_user(new_member)

            try:
                GroupMember.get(
                    (GroupMember.group_id == g.group_id)
                    & (GroupMember.bakchod_id == b.tg_id)
                )
            except DoesNotExist:

                logger.info(
                    "[status_update] bakchod={} has joined group={}",
                    b.tg_id,
                    g.group_id,
                )

                GroupMember.create(group=g, bakchod=b)

    # Handle left_chat_member
    left_chat_member = update.message.left_chat_member

    if left_chat_member is not None:

        b = bakchod.get_or_create_bakchod_from_tg_user(left_chat_member)

        logger.info("[status_update] bakchod={} has left group={}", b.tg_id, g.group_id)

        GroupMember.delete().where(
            (GroupMember.group_id == g.group_id) & (GroupMember.bakchod_id == b.tg_id)
        ).execute()
