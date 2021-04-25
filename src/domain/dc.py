from datetime import datetime
from loguru import logger
from telegram import Update
from src.db import bakchod, group, message
from . import util
from . import metrics


def log_command_usage(command_name: str, update: Update):

    logger.info(
        "[dc] {} invoked. user='{}' group='{}'",
        command_name,
        util.extract_pretty_name_from_tg_user(update.message.from_user),
        update.message.chat.title,
    )

    sync_persistence_data(update)

    metrics.inc_command_usage_count(command_name, update)

    return


def sync_persistence_data(update: Update):

    if hasattr(update.message, "from_user"):
        from_user = update.message.from_user
    else:
        logger.debug("[dc] update had no message.from_user... fast failing")
        return

    b = bakchod.get_or_create_bakchod_from_tg_user(from_user)

    # Update username
    b.username = from_user.username

    # Update prettyname
    b.pretty_name = util.extract_pretty_name_from_tg_user(from_user)

    # Update lastseen of Bakchod
    b.lastseen = datetime.now()

    b.updated = datetime.now()

    b.save()

    message.log_message_from_update(update)

    group.log_group_from_update(update)

    return