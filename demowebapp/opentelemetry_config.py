"""
OpenTelemetry configuration for Azure Monitor
This module provides a more controlled way to configure OpenTelemetry
to avoid attribute type conflicts.
"""
import os
import logging
from typing import Dict, Any

def configure_opentelemetry_safe() -> bool:
    """
    Safely configure OpenTelemetry with Azure Monitor.
    
    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        # Import OpenTelemetry components
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
        
        # Create resource with safe attributes
        resource_attributes: Dict[str, Any] = {
            "service.name": "demo-webapp",
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "production"),
        }
        
        # Only add non-None values to avoid type issues
        resource_attributes = {k: v for k, v in resource_attributes.items() if v is not None}
        
        resource = Resource.create(resource_attributes)
        
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider(resource=resource))
        tracer_provider = trace.get_tracer_provider()
        
        # Configure Azure Monitor exporter
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if not connection_string:
            logging.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set")
            return False
            
        exporter = AzureMonitorTraceExporter(
            connection_string=connection_string
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)
        
        logging.info("OpenTelemetry configured successfully with Azure Monitor")
        return True
        
    except Exception as e:
        logging.error(f"Failed to configure OpenTelemetry: {e}")
        return False

def configure_opentelemetry_logging() -> bool:
    """
    Configure OpenTelemetry logging with Azure Monitor.
    
    Returns:
        bool: True if configuration was successful, False otherwise
    """
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
        from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
        
        # Create resource with safe attributes
        resource_attributes: Dict[str, Any] = {
            "service.name": "demo-webapp",
            "service.version": "1.0.0",
        }
        
        resource = Resource.create(resource_attributes)
        
        # Set up logger provider
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)
        
        # Configure Azure Monitor log exporter
        connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
        if not connection_string:
            return False
            
        log_exporter = AzureMonitorLogExporter(
            connection_string=connection_string
        )
        
        # Add log record processor
        log_processor = BatchLogRecordProcessor(log_exporter)
        logger_provider.add_log_record_processor(log_processor)
        
        logging.info("OpenTelemetry logging configured successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to configure OpenTelemetry logging: {e}")
        return False
