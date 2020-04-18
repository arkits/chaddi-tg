from loguru import logger
from db import dao
from models.bakchod import Bakchod
from models.group import Group
from domain import bakchod as bakchod_domain
import time
import datetime
from handlers import bestie, hi, roll
import traceback
from util import util


def all(update, context):

    # Update Bakchod DB
    bakchod = dao.get_bakchod_by_id(update.message.from_user.id)

    if bakchod is None:
        bakchod = Bakchod.fromUpdate(update)
        logger.info("Looks like we have a new Bakchod! - {}", bakchod.__dict__)

    bakchod = update_bakchod(bakchod, update)

    # Update Group DB
    group = dao.get_group_by_id(update.message.chat.id)

    if group is None:
        group = Group.fromUpdate(update)
        logger.info("Looks like we have a new Group! - {}", group.__dict__)

    update_group(group, bakchod, update)

    # Log this
    logger.info(
        "[default.all] b.username='{}' b.rokda={} g.title='{}'",
        util.extract_pretty_name_from_bakchod(bakchod),
        bakchod.rokda,
        group.title,
    )

    handle_bakchod_modifiers(update, context, bakchod)

    handle_dice_rolls(update, context)

    handle_message_matching(update, context)


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


def handle_dice_rolls(update, context):

    dice = update.message.dice

    if dice is not None:

        roll.handle_dice_rolls(dice.value, update, context)

    return


def handle_bakchod_modifiers(update, context, bakchod):

    bot = context.bot

    modifiers = bakchod.modifiers
    logger.info(modifiers)

    try:

        if "censored" in modifiers.keys():

            if modifiers["censored"] == True:

                logger.info(
                    "[modifiers] censoring {}",
                    util.extract_pretty_name_from_bakchod(bakchod),
                )

                try:
                    bot.delete_message(
                        chat_id=update.message.chat_id,
                        message_id=update.message.message_id,
                    )
                except Exception as e:
                    logger.error(
                        "Caught Error in censoring Bakchod - {} \n {}",
                        e,
                        traceback.format_exc(),
                    )
                    bot.send_message(
                        chat_id=update.message.chat_id,
                        text="Looks like I'm not able to delete messages... Please check the Group permissions!",
                    )

    except Exception as e:
        logger.error(
            "Caught Error in default.handle_bakchod_modifiers - {} \n {}",
            e,
            traceback.format_exc(),
        )

    return
