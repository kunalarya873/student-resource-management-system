import logging

from app.core.telemetry import get_logger_provider, setup_telemetry, shutdown_telemetry


def test_telemetry_lifecycle():
    # Setup
    provider = setup_telemetry()
    assert provider is not None
    assert get_logger_provider() is not None

    # Verify standard library logging bridge works without exceptions
    test_logger = logging.getLogger("test_telemetry")
    test_logger.info("Test log message for OpenTelemetry bridge")

    # Shutdown
    shutdown_telemetry()
    assert get_logger_provider() is None
