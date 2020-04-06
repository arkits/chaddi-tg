from loguru import logger
from util import config

chaddi_config = config.get_config()


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


def is_admin(og_bakchod):

    allowed_setters = chaddi_config["allowed_setters"]

    if str(og_bakchod) in allowed_setters:
        logger.info("[is_admin] og_bakchod={} in config.allowed_setters", og_bakchod)
        return True
    else:
        return False

def extract_pretty_name(from_user):

    if from_user["username"]:
        from_user = "@" + from_user["username"]
    elif from_user["firstname"]:
        from_user = from_user["firstname"]

    return from_user