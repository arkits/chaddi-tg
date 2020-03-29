from loguru import logger


def print_title():
    print("~~~~ ~~~~ ~~~~ ~~~~")
    print("🙏 ChaddiBot 🙏")
    print("~~~~ ~~~~ ~~~~ ~~~~")


def log_chat(handler_name, update):
    logger.info(
        "[{}] Handling request from user '{}' in group '{}'",
        handler_name,
        update.message.from_user["username"],
        update.message.chat.title,
    )
