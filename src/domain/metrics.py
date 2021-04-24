from loguru import logger
from prometheus_client import Counter
from telegram import Update

message_counter = Counter(
    "chaddi_messages_count", "chaddi_messages_count", ["group_id", "group_name"]
)

command_usage_counter = Counter(
    "chaddi_command_usage_count",
    "chaddi_command_usage_count",
    ["group_id", "group_name"],
)


def inc_message_count(update: Update):
    message_counter.labels(
        group_id=update.message.chat.id, group_name=update.message.chat.title
    ).inc()
    return


def inc_command_usage_count(update: Update):
    command_usage_counter.labels(
        group_id=update.message.chat.id, group_name=update.message.chat.title
    ).inc()
    return