from prometheus_client import start_http_server, Counter
from util import config, util
from loguru import logger

# Get application config
chaddi_config = config.get_config()


message_counter = Counter(
    "chaddi_messages_count", "chaddi_messages_count", ["group_id"]
)

rolls_started = Counter("chaddi_rolls_started", "chaddi_rolls_started")
rolls_won = Counter("chaddi_rolls_won", "chaddi_rolls_won")
rolls_attempted = Counter("chaddi_rolls_attempted", "rolls_attempted")

gamble_counter = Counter("chaddi_gamble_count", "chaddi_gamble_count", ["user_id"])

mom_invoker_counter = Counter(
    "chaddi_mom_invoker_count", "chaddi_mom_invoker_count", ["user_id"]
)
mom_victim_counter = Counter(
    "chaddi_mom_victim_count", "chaddi_mom_victim_count", ["user_id"]
)

mom2_invoker_counter = Counter(
    "chaddi_mom2_invoker_count", "chaddi_mom2_invoker_count", ["user_id"]
)
mom2_victim_counter = Counter(
    "chaddi_mom2_victim_count", "chaddi_mom2_victim_count", ["user_id"]
)


def serve_metrics():
    logger.info("Serving Metrics on port={}", chaddi_config["metrics"]["port"])
    start_http_server(chaddi_config["metrics"]["port"])
    return


def inc_message_count(update):
    message_counter.labels(group_id=update.message.chat.id).inc()
    return


def inc_gamble_count(update):
    gamble_counter.labels(user_id=update.message.from_user["id"]).inc()
    return
