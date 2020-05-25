from loguru import logger
from util import util
from db import dao
import traceback


def handle(update, context):

    util.log_chat("reset", update)

    try:

        # Extract query...
        query = update.message.text
        query = query.split(" ")

        target = None

        if not util.is_admin(update.message.from_user["id"]):
            return

        # Request includes the username as a mention
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "text_mention" and entity.user is not None:
                    target = dao.get_bakchod_by_id(entity.user.id)

        # Last attempt... try to lookup username in DB
        if target is None:

            receiver_username = query[1]

            # Remove the "@" prefix
            if receiver_username.startswith("@"):
                receiver_username = receiver_username[1:]

            target = dao.get_bakchod_by_username(receiver_username)

        if target is not None:
            logger.info(
                "[reset] target={}", util.extract_pretty_name_from_bakchod(target)
            )
            target.modifiers = {}
            dao.insert_bakchod(target)
            update.message.reply_text(
                "Reset - " + util.extract_pretty_name_from_bakchod(target)
            )
            return

    except Exception as e:
        logger.error(
            "Caught Error in quotes.handle - {} \n {}", e, traceback.format_exc(),
        )
