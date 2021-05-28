from loguru import logger
from prometheus_client import Counter
from telegram import Update

messages_count = Counter(
    "chaddi_messages_count", "chaddi_messages_count", ["group_id", "group_name"]
)

command_usage_count = Counter(
    "chaddi_command_usage_count",
    "chaddi_command_usage_count",
    ["group_id", "group_name", "command_name"],
)


def inc_message_count(update: Update):
    messages_count.labels(
        group_id=update.message.chat.id, group_name=update.message.chat.title
    ).inc()
    return


def inc_command_usage_count(command_name: str, update: Update):
    command_usage_count.labels(
        group_id=update.message.chat.id,
        group_name=update.message.chat.title,
        command_name=command_name,
    ).inc()
    return