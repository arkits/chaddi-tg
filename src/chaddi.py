import asyncio

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.openai import OpenAIIntegration

# Import config first to get Sentry environment before initializing Sentry
from src.domain import config

app_config = config.get_config()

# Initialize Sentry SDK BEFORE importing any modules that use OpenAI
# This ensures Sentry can instrument the OpenAI client when it's created
sentry_sdk.init(
    dsn="https://b28179ae59e491947ce4cb052ab4c3fc@o425745.ingest.us.sentry.io/4510605721141248",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
    environment=app_config.get("SENTRY", "ENVIRONMENT", fallback="dev"),
    enable_logs=True,
    integrations=[
        OpenAIIntegration(
            include_prompts=True,  # LLM/tokenizer inputs/outputs will be not sent to Sentry, despite send_default_pii=True
        ),
    ],
)

# Now import modules that use OpenAI - Sentry will have already instrumented it
from src.bot import run_telegram_bot  # noqa: E402
from src.domain import otel_logging  # noqa: E402
from src.server import run_server  # noqa: E402

# Initialize OpenTelemetry logging for PostHog
otel_logging.setup_otel_logging()


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
