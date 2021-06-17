from datetime import datetime
import json
from loguru import logger
from peewee import DoesNotExist
from telegram import Update
from telegram.ext import CallbackContext
from src.domain import dc
from src.db import Bakchod, EMPTY_JSON, GroupMember, bakchod, group
from . import hi, bestie


def all(update: Update, context: CallbackContext) -> None:
    dc.sync_persistence_data(update)

    # If the update was related to a message send from a user...
    if hasattr(update.message, "from_user"):
        from_user = update.message.from_user
    else:
        logger.debug("[all] update had no message.from_user... fast failing")
        return

    # Reward rokda to Bakchod
    b = bakchod.get_or_create_bakchod_from_tg_user(from_user)
    b.rokda = reward_rokda(b.rokda)
    b.updated = datetime.now()
    b.save()

    handle_bakchod_metadata_effects(update, context, b)

    handle_message_matching(update, context)


def handle_bakchod_metadata_effects(
    update: Update, context: CallbackContext, bakchod: Bakchod
):

    if bakchod.metadata is None:
        return

    if bakchod.metadata == EMPTY_JSON:
        return

    try:

        metadata = json.loads(bakchod.metadata)

        for key in metadata:

            if key == "route-messages":

                rm = metadata[key]

                for route_message_props in rm:

                    # if the message is posted to the same group, then ignore it
                    if str(route_message_props["to_group"]) == str(
                        update.message.chat_id
                    ):

                        logger.trace(
                            "route-messages - posted in the same group - {} // {}",
                            route_message_props["to_group"],
                            update.message.chat_id,
                        )

                        continue

                    context.bot.forward_message(
                        chat_id=route_message_props["to_group"],
                        from_chat_id=update.message.chat_id,
                        message_id=update.message.message_id,
                    )

    except Exception as e:
        logger.error("Caught Exception in handle_bakchod_metadata_effects - e={}", e)

    return


def handle_message_matching(update: Update, context: CallbackContext):

    message_text = update.message.text

    if message_text is not None:

        # Handle 'hi' messages
        if "hi" == message_text.lower():
            hi.handle(update, context, log_to_dc=False)

        # Handle bestie messages
        if "bestie" in message_text.lower():
            bestie.handle(update, context, log_to_dc=False)

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
