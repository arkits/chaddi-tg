import configparser
import os
from loguru import logger

profile_name = os.getenv("CHADDI_BOT_PROFILE")
if profile_name is None:
    # Default to dev profile - intended for local dev
    profile_name = "dev"

config = configparser.ConfigParser()

logger.debug("cwd is {}", os.getcwd())
logger.info("Loading config - {}", profile_name)
config.read("config/{}.ini".format(profile_name))


def get_config():
    return config
