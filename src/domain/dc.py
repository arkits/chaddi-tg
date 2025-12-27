import asyncio
import json
import traceback
from datetime import datetime

import sentry_sdk
from loguru import logger
from playhouse.shortcuts import model_to_dict
from telegram import Update

from src.db import Bakchod, CommandUsage, Group, bakchod_dao, group_dao, message_dao
from src.server import sio

from . import analytics, metrics, util


def log_command_usage(command_name: str, update: Update):
    try:
        if not hasattr(update, "message"):
            logger.debug("[dc] update had no message... fast failing")
            return

        from_user = update.message.from_user
        chat = update.message.chat
        user_name = util.extract_pretty_name_from_tg_user(from_user)
        group_name = chat.title

        logger.info(
            "[dc] {} invoked. user='{}' group='{}'",
            command_name,
            user_name,
            group_name,
        )

        # Sentry: Add breadcrumb and context
        sentry_sdk.add_breadcrumb(
            category="command",
            message=f"Command {command_name} invoked",
            level="info",
            data={"user": user_name, "group": group_name},
        )

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("command", command_name)
            scope.set_tag("module", "dc.log_command_usage")
            scope.set_context(
                "telegram",
                {
                    "user_id": str(from_user.id),
                    "username": from_user.username,
                    "chat_id": str(chat.id),
                    "chat_type": chat.type,
                    "chat_title": group_name,
                },
            )

            # PostHog: Track command usage event
            try:
                analytics.posthog.capture(
                    distinct_id=str(from_user.id),
                    event="command_used",
                    properties={
                        "command_name": command_name,
                        "user_id": str(from_user.id),
                        "username": from_user.username,
                        "user_name": user_name,
                        "chat_id": str(chat.id),
                        "chat_type": chat.type,
                        "chat_title": group_name,
                    },
                )
            except Exception as ph_error:
                logger.warning("[dc] Failed to send PostHog event: {}", ph_error)

            sync_persistence_data(update)

            # Log command usage to database
            try:
                bakchod = Bakchod.get(Bakchod.tg_id == from_user.id)
                group = Group.get(Group.group_id == chat.id)

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
                # Sentry: Capture database error (scope context already set)
                sentry_sdk.capture_exception(db_error)

            metrics.inc_command_usage_count(command_name, update)

        return

    except Exception as e:
        logger.error(
            "Caught Error in dc.log_command_usage - {} \n {}",
            e,
            traceback.format_exc(),
        )
        # Sentry: Capture exception
        sentry_sdk.capture_exception(e)
        return


def sync_persistence_data(update: Update):
    if hasattr(update.message, "from_user"):
        from_user = update.message.from_user
    else:
        logger.debug("[dc] update had no message.from_user... fast failing")
        return

    try:
        # Sentry: Add context for sync operation
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("module", "dc.sync_persistence_data")
            scope.set_context(
                "telegram",
                {
                    "user_id": str(from_user.id),
                    "username": from_user.username,
                    "chat_id": str(update.message.chat.id),
                    "chat_type": update.message.chat.type,
                },
            )

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

            # PostHog: Track message sync event
            try:
                analytics.posthog.capture(
                    distinct_id=str(from_user.id),
                    event="message_synced",
                    properties={
                        "user_id": str(from_user.id),
                        "username": from_user.username,
                        "chat_id": str(update.message.chat.id),
                        "chat_type": update.message.chat.type,
                        "chat_title": update.message.chat.title,
                        "message_id": str(update.message.message_id),
                    },
                )
            except Exception as ph_error:
                logger.debug("[dc] Failed to send PostHog sync event: {}", ph_error)

            # Create a task to emit the message asynchronously without blocking
            asyncio.create_task(
                sio.emit(
                    "message",
                    {"message": json.loads(json.dumps(model_to_dict(m), default=str))},
                )
            )

    except Exception as e:
        logger.error(
            "Caught Error in dc.sync_persistence_data - {} \n {}",
            e,
            traceback.format_exc(),
        )
        # Sentry: Capture exception
        sentry_sdk.capture_exception(e)
        raise

    return
