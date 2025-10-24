import asyncio
import json
import traceback
from datetime import datetime

from loguru import logger
from playhouse.shortcuts import model_to_dict
from telegram import Update

from src.db import Bakchod, CommandUsage, Group, bakchod_dao, group_dao, message_dao
from src.server import sio

from . import metrics, util


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

        # Log command usage to database
        try:
            bakchod = Bakchod.get(Bakchod.tg_id == update.message.from_user.id)
            group = Group.get(Group.group_id == update.message.chat.id)

            CommandUsage.create(
                command_name=command_name,
                executed_at=datetime.now(),
                from_bakchod=bakchod,
                group=group,
            )
        except Exception as db_error:
            logger.warning(
                "[dc] Failed to log command usage to database: {}",
                db_error,
            )

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

    # Create a task to emit the message asynchronously without blocking
    asyncio.create_task(
        sio.emit(
            "message",
            {"message": json.loads(json.dumps(model_to_dict(m), default=str))},
        )
    )

    return
