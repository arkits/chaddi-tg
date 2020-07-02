import json

with open("resources/config.json") as config:
    config = json.load(config)


def get_config():
    return config
