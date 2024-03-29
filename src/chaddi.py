import threading
from loguru import logger

# from src.domain import logger as domain_logger

from src.server import run_server
from src.bot import run_telegram_bot


def main():

    logger.info("Starting chaddi-tg _/\_")

    # Uncomment to intercept debug logs from other libs
    # domain_logger.intercept_logs_with_loguru()

    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    run_telegram_bot()


if __name__ == "__main__":
    main()
