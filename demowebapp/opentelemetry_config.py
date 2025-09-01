"""
Performance-optimized OpenTelemetry configuration for Azure Monitor
This module provides optimized OpenTelemetry configuration to minimize resource usage
while maintaining essential monitoring capabilities.
"""

import logging
import os
from typing import Any, Dict


def get_service_resource_attributes() -> Dict[str, Any]:
    """
    Get minimal service resource attributes to reduce overhead.

    Returns:
        Dict[str, Any]: Essential resource attributes for the service
    """
    attributes = {
        "service.name": "demo-webapp",
        "service.version": "1.0.0",
    }

    # Only add environment if explicitly set to avoid unnecessary attributes
    environment = os.getenv("ENVIRONMENT")
    if environment and environment.lower() in ["production", "staging", "development"]:
        attributes["deployment.environment"] = environment

    return attributes


def configure_opentelemetry_safe() -> bool:
    """
    Configure optimized OpenTelemetry tracing with performance settings.

    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logging.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set")
            return False

        # Create minimal resource attributes
        resource_attributes = get_service_resource_attributes()
        resource = Resource.create(resource_attributes)

        # Configure sampling to reduce volume (sample 10% of traces by default)
        sampling_rate = float(os.getenv("AZURE_MONITOR_SAMPLING_RATE", "0.1"))  # 10% by default
        sampler = TraceIdRatioBased(sampling_rate)

        # Set up tracer provider with sampling
        trace.set_tracer_provider(TracerProvider(resource=resource, sampler=sampler))
        tracer_provider = trace.get_tracer_provider()

        # Configure Azure Monitor exporter
        exporter = AzureMonitorTraceExporter(connection_string=connection_string)

        # Optimized batch processor settings
        max_queue_size = int(os.getenv("AZURE_MONITOR_MAX_QUEUE_SIZE", "512"))
        export_timeout = int(os.getenv("AZURE_MONITOR_EXPORT_TIMEOUT", "30000"))
        schedule_delay = int(os.getenv("AZURE_MONITOR_SCHEDULE_DELAY", "5000"))
        max_batch_size = int(os.getenv("AZURE_MONITOR_MAX_EXPORT_BATCH_SIZE", "128"))

        span_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=max_queue_size,
            export_timeout_millis=export_timeout,
            schedule_delay_millis=schedule_delay,
            max_export_batch_size=max_batch_size,
        )
        tracer_provider.add_span_processor(span_processor)

        logging.info(f"Optimized OpenTelemetry tracing configured with {sampling_rate*100}% sampling")
        return True

    except Exception as e:
        logging.error(f"Failed to configure optimized OpenTelemetry tracing: {e}")
        return False


def configure_opentelemetry_logging() -> bool:
    """
    Configure optimized OpenTelemetry logging with performance settings.

    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource

        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logging.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set for logging")
            return False

        # Create minimal resource attributes
        resource_attributes = get_service_resource_attributes()
        resource = Resource.create(resource_attributes)

        # Set up logger provider
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        # Configure Azure Monitor log exporter
        log_exporter = AzureMonitorLogExporter(connection_string=connection_string)

        # Optimized batch processor for logs
        max_queue_size = int(os.getenv("AZURE_MONITOR_MAX_QUEUE_SIZE", "512"))
        export_timeout = int(os.getenv("AZURE_MONITOR_EXPORT_TIMEOUT", "30000"))
        schedule_delay = int(os.getenv("AZURE_MONITOR_SCHEDULE_DELAY", "5000"))
        max_batch_size = int(os.getenv("AZURE_MONITOR_MAX_EXPORT_BATCH_SIZE", "128"))

        log_processor = BatchLogRecordProcessor(
            log_exporter,
            max_queue_size=max_queue_size,
            export_timeout_millis=export_timeout,
            schedule_delay_millis=schedule_delay,
            max_export_batch_size=max_batch_size,
        )
        logger_provider.add_log_record_processor(log_processor)

        logging.info("Optimized OpenTelemetry logging configured successfully")
        return True

    except Exception as e:
        logging.error(f"Failed to configure optimized OpenTelemetry logging: {e}")
        return False


def configure_opentelemetry_metrics() -> bool:
    """
    Configure optimized OpenTelemetry metrics with reduced frequency.

    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter
        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource

        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logging.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set for metrics")
            return False

        # Create minimal resource attributes
        resource_attributes = get_service_resource_attributes()
        resource = Resource.create(resource_attributes)

        # Configure Azure Monitor metric exporter
        metric_exporter = AzureMonitorMetricExporter(connection_string=connection_string)

        # Optimized metric reader with less frequent exports
        export_interval = int(os.getenv("AZURE_MONITOR_METRICS_INTERVAL", "300000"))  # 5 minutes by default
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=export_interval,
        )

        # Set up meter provider
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

        logging.info(f"Optimized OpenTelemetry metrics configured with {export_interval/1000}s intervals")
        return True

    except Exception as e:
        logging.error(f"Failed to configure optimized OpenTelemetry metrics: {e}")
        return False


def configure_selective_instrumentation():
    """
    Configure only essential instrumentation to reduce overhead.

    Returns:
        bool: True if instrumentation was successful
    """
    try:
        # Only instrument essential components
        from opentelemetry.instrumentation.django import DjangoInstrumentor

        # Configure Django instrumentation with minimal settings
        DjangoInstrumentor().instrument(
            request_hook=None,  # Disable request hooks to reduce overhead
            response_hook=None,  # Disable response hooks to reduce overhead
        )

        # Only instrument database if specifically needed
        if os.getenv("AZURE_MONITOR_INSTRUMENT_DB", "false").lower() == "true":
            from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

            Psycopg2Instrumentor().instrument()

        # Only instrument HTTP requests if specifically needed
        if os.getenv("AZURE_MONITOR_INSTRUMENT_HTTP", "false").lower() == "true":
            from opentelemetry.instrumentation.requests import RequestsInstrumentor

            RequestsInstrumentor().instrument()

        logging.info("Selective instrumentation configured successfully")
        return True

    except Exception as e:
        logging.error(f"Failed to configure selective instrumentation: {e}")
        return False
