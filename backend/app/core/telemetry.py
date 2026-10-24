import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from app.core.config import settings

logger = logging.getLogger("amu_backend.telemetry")

_logger_provider: LoggerProvider | None = None
_otel_logging_handler: LoggingHandler | None = None


def setup_telemetry() -> LoggerProvider | None:
    """
    Configure and initialize OpenTelemetry logging provider with PostHog OTLP exporter,
    and bridge standard library logging to OTel.
    """
    global _logger_provider, _otel_logging_handler

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry logging is disabled (OTEL_ENABLED=false).")
        return None

    if _logger_provider is not None:
        return _logger_provider

    try:
        # Define OTel Resource with service identification
        resource = Resource(attributes={"service.name": settings.OTEL_SERVICE_NAME})

        # Initialize LoggerProvider
        _logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(_logger_provider)

        # Set up PostHog OTLP HTTP log exporter
        headers: dict[str, str] = {}
        if settings.POSTHOG_API_KEY:
            headers["Authorization"] = f"Bearer {settings.POSTHOG_API_KEY}"

        exporter = OTLPLogExporter(
            endpoint=settings.POSTHOG_LOGS_ENDPOINT,
            headers=headers,
        )

        # Batch log record processor for async, non-blocking telemetry exports
        _logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

        # Bridge standard library logging to OpenTelemetry
        _otel_logging_handler = LoggingHandler(logger_provider=_logger_provider)
        root_logger = logging.getLogger()
        root_logger.addHandler(_otel_logging_handler)
        root_logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

        logger.info(
            f"OpenTelemetry logging initialized for service '{settings.OTEL_SERVICE_NAME}' "
            f"exporting to '{settings.POSTHOG_LOGS_ENDPOINT}'."
        )
        return _logger_provider
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Failed to initialize OpenTelemetry logging: {exc}")
        return None


def get_logger_provider() -> LoggerProvider | None:
    """Return the currently configured LoggerProvider instance if any."""
    return _logger_provider


def shutdown_telemetry() -> None:
    """Flush and shutdown the LoggerProvider and remove logging handler."""
    global _logger_provider, _otel_logging_handler

    if _otel_logging_handler is not None:
        try:
            logging.getLogger().removeHandler(_otel_logging_handler)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"Failed to remove OTel logging handler: {exc}")
        _otel_logging_handler = None

    if _logger_provider is not None:
        try:
            _logger_provider.shutdown()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Error during OpenTelemetry LoggerProvider shutdown: {exc}")
        finally:
            _logger_provider = None
