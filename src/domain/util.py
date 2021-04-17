from loguru import logger
from telegram import Update


def log_chat(handler_name: str, update: Update):

    pretty_name = "A Chutiya"

    try:
        if update.message.from_user["username"] is not None:
            pretty_name = update.message.from_user["username"]
        elif update.message.from_user["first_name"] is not None:
            pretty_name = update.message.from_user["first_name"]
        elif update.message.from_user["id"] is not None:
            pretty_name = update.message.from_user["id"]
    except Exception as e:
        pass

    try:
        logger.info(
            "[{}] Handling request from user '{}' in group '{}'",
            handler_name,
            pretty_name,
            update.message.chat.title,
        )
    except Exception as e:
        # This is by design... logging shouldn't throw an Error,
        # only my terrible coding should!
        pass
