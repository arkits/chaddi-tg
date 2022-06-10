from datetime import datetime
import json
import traceback
from loguru import logger
from telegram import Update
from src.db import bakchod_dao, group_dao, message_dao
from . import util
from . import metrics
from src.server import socket_manager
import asyncio
from playhouse.shortcuts import model_to_dict


def log_command_usage(command_name: str, update: Update):

    try:

        if not hasattr(update, "message"):
            logger.debug("[dc] update had no message... fast failing")
            return

        logger.info(
            "[dc] {} invoked. user='{}' group='{}'",
            command_name,
            util.extract_pretty_name_from_tg_user(update.message.from_user),
            update.message.chat.title,
        )

        sync_persistence_data(update)

        metrics.inc_command_usage_count(command_name, update)

        return

    except Exception as e:
        logger.error(
            "Caught Error in dc.log_command_usage - {} \n {}",
            e,
            traceback.format_exc(),
        )
        return


def sync_persistence_data(update: Update):

    if hasattr(update.message, "from_user"):
        from_user = update.message.from_user
    else:
        logger.debug("[dc] update had no message.from_user... fast failing")
        return

    b = bakchod_dao.get_or_create_bakchod_from_tg_user(from_user)

    # Update username
    b.username = from_user.username

    # Update prettyname
    b.pretty_name = util.extract_pretty_name_from_tg_user(from_user)

    # Update lastseen of Bakchod
    b.lastseen = datetime.now()

    b.updated = datetime.now()

    b.save()

    m = message_dao.log_message_from_update(update)

    group_dao.log_group_from_update(update)

    asyncio.run(
        socket_manager.emit(
            "message",
            {"message": json.loads(json.dumps(model_to_dict(m), default=str))},
        )
    )

    return
