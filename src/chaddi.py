import threading
import os
from loguru import logger

from util import logger as logger_util

from server import run_server
from bot import run_telegram_bot


def main():

    logger.info("Starting chaddi-tg _/\_")
    logger.debug("cwd is {}", os.getcwd())

    # Uncomment to intercept debug logs from other libs
    # logger_util.intercept_logs_with_loguru()

    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    run_telegram_bot()


if __name__ == "__main__":
    main()
