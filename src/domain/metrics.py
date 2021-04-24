from loguru import logger
from prometheus_client import Counter
from telegram import Update

message_counter = Counter(
    "chaddi_messages_count", "chaddi_messages_count", ["group_id", "group_name"]
)


def inc_message_count(update: Update):
    message_counter.labels(
        group_id=update.message.chat.id, group_name=update.message.chat.title
    ).inc()
    return