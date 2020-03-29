import json
from loguru import logger

config_file = open("resources/config.json", "r")
config = json.loads(config_file.read())


def get_config():
    return config
