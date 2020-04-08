from loguru import logger
from util import config
import json

chaddi_config = config.get_config()

# Read verbLookupTable on startup
verbLookupTable_file = open("resources/verbPastLookup.json", "r")
verbLookupTable = json.loads(verbLookupTable_file.read())


def get_verbLookupTable():
    return verbLookupTable


def print_title():
    print("~~~~ ~~~~ ~~~~ ~~~~")
    print("🙏 ChaddiBot 🙏")
    print("~~~~ ~~~~ ~~~~ ~~~~")


def log_chat(handler_name, update):

    pretty_name = "None"

    try:
        if update.message.from_user["username"] is not None:
            pretty_name = update.message.from_user["username"]
        elif update.message.from_user["first_name"] is not None:
            pretty_name = update.message.from_user["first_name"]
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



def is_admin(og_bakchod):

    allowed_setters = chaddi_config["allowed_setters"]

    if str(og_bakchod) in allowed_setters:
        logger.info("[is_admin] og_bakchod={} in config.allowed_setters", og_bakchod)
        return True
    else:
        return False
