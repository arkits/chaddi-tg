from datetime import datetime
from loguru import logger
from telegram import Update
from src.db import bakchod, group, message
from . import util


def log_command_usage(command_name: str, update: Update):

    logger.info(
        "[dc] {} invoked. user='{}' group='{}'",
        command_name,
        util.extract_pretty_name_from_tg_user(update.message.from_user),
        update.message.chat.title,
    )

    sync_persistence_data(update)

    return


def sync_persistence_data(update: Update):

    b = bakchod.get_bakchod_from_update(update)

    # Update lastseen of Bakchod
    b.lastseen = datetime.now()
    b.updated = datetime.now()
    b.save()

    message.log_message_from_update(update)

    group.log_group_from_update(update)

    return