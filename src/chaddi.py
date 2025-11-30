import asyncio

from loguru import logger

from src.bot import run_telegram_bot

# from src.domain import logger as domain_logger
from src.server import run_server


async def main():
    logger.info(r"Starting chaddi-tg _/\_")

    # Uncomment to intercept debug logs from other libs
    # domain_logger.intercept_logs_with_loguru()

    # Run both the bot and server concurrently using asyncio
    try:
        await asyncio.gather(
            run_telegram_bot(),
            run_server(),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down chaddi-tg...")


if __name__ == "__main__":
    asyncio.run(main())
