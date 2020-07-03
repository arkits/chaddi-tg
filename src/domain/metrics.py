from prometheus_client import start_http_server
from util import config, util
from loguru import logger

# Get application config
chaddi_config = config.get_config()


def serve_metrics():
    logger.info("Serving Metrics on port={}", chaddi_config["metrics"]["port"])
    start_http_server(chaddi_config["metrics"]["port"])