import configparser
from loguru import logger

profile_name = "dev"

config = configparser.ConfigParser()

logger.info("Loading config - {}", profile_name)
config.read("config/{}.ini".format(profile_name))


def get_config():
    return config