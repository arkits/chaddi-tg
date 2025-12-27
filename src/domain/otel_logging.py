"""OpenTelemetry logging integration for loguru."""

from loguru import logger
from opentelemetry._logs import LogRecord, get_logger, set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from . import config

app_config = config.get_config()


def setup_otel_logging():
    """Set up OpenTelemetry logging integration with loguru."""
    try:
        # Get PostHog API key from config
        posthog_api_key = app_config.get("POSTHOG", "API_KEY", fallback=None)

        if not posthog_api_key or posthog_api_key == "YOUR_POSTHOG_API_KEY":
            logger.warning(
                "[otel] PostHog API key not configured, skipping OpenTelemetry logging setup"
            )
            return

        # Configure the logger provider
        logger_provider = LoggerProvider()
        set_logger_provider(logger_provider)

        # Create OTLP exporter with token in header
        otlp_exporter = OTLPLogExporter(
            endpoint="https://us.i.posthog.com/i/v1/logs",
            headers={"Authorization": f"Bearer {posthog_api_key}"},
        )

        # Add processor
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

        # Get OpenTelemetry logger
        otel_logger = get_logger("chaddi-tg")

        # Create a custom sink function that bridges loguru to OpenTelemetry
        def loguru_to_otel_sink(message):
            """Convert loguru log record to OpenTelemetry log record."""
            record = message.record

            # Map loguru levels to OpenTelemetry severity numbers
            # OpenTelemetry uses: TRACE=1, DEBUG=5, INFO=9, WARN=13, ERROR=17, FATAL=21
            level_mapping = {
                "TRACE": 1,
                "DEBUG": 5,
                "INFO": 9,
                "SUCCESS": 9,  # Map SUCCESS to INFO
                "WARNING": 13,
                "ERROR": 17,
                "CRITICAL": 21,
            }
            severity_number = level_mapping.get(record["level"].name, 9)

            # Create attributes from record
            attributes = {
                "logger.name": record["name"],
                "code.filepath": str(record["file"].path) if record["file"] else None,
                "code.lineno": record["line"],
                "code.function": record["function"],
                "thread.id": record["thread"].id if record["thread"] else None,
                "thread.name": record["thread"].name if record["thread"] else None,
                "process.id": record["process"].id if record["process"] else None,
                "process.name": record["process"].name if record["process"] else None,
            }

            # Remove None values
            attributes = {k: v for k, v in attributes.items() if v is not None}

            # Get the formatted message
            formatted_message = str(message)

            # Emit log record to OpenTelemetry
            otel_logger.emit(
                LogRecord(
                    timestamp=int(
                        record["time"].timestamp() * 1_000_000_000
                    ),  # Convert to nanoseconds
                    severity_number=severity_number,
                    severity_text=record["level"].name,
                    body=formatted_message,
                    attributes=attributes,
                    trace_id=None,  # Could be populated if tracing is enabled
                    span_id=None,  # Could be populated if tracing is enabled
                )
            )

        # Add the custom sink to loguru
        # Note: We don't remove the default handler to preserve existing console logging
        # Add OpenTelemetry sink as an additional handler
        logger.add(
            loguru_to_otel_sink,
            format="{message}",
            level="DEBUG",
            serialize=False,  # We're handling serialization manually
        )

        logger.info("[otel] OpenTelemetry logging initialized successfully")

    except Exception as e:
        logger.error(
            "[otel] Failed to initialize OpenTelemetry logging: {}",
            e,
            exc_info=True,
        )
