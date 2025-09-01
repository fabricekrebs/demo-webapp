#!/usr/bin/env python3
"""
Test script to verify Application Insights integration
"""
import logging
import os
import sys
import time

import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, "/home/krfa/git-repo/demo-webapp")

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demowebapp.settings")

# Initialize Django
django.setup()


def test_application_insights():
    """Test Application Insights integration"""
    print("🧪 Testing Application Insights Integration...")
    print(f"ENABLE_AZURE_MONITOR: {getattr(settings, 'ENABLE_AZURE_MONITOR', 'Not set')}")

    if not getattr(settings, "ENABLE_AZURE_MONITOR", False):
        print("❌ Azure Monitor is not enabled")
        return False

    print("✅ Azure Monitor is enabled")

    # Test logging
    logger = logging.getLogger(__name__)
    print("📝 Sending test log messages...")

    logger.info("🧪 Test INFO log message for Application Insights")
    logger.warning("⚠️ Test WARNING log message for Application Insights")
    logger.error("❌ Test ERROR log message for Application Insights")

    # Test OpenTelemetry tracing if configured
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)

        print("📊 Testing OpenTelemetry tracing...")
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("test.attribute", "test_value")
            span.set_attribute("test.number", 42)
            span.add_event("test_event", {"event.data": "test_data"})
            print("✅ Test span created successfully")
            time.sleep(0.1)  # Small delay to simulate work

    except Exception as e:
        print(f"⚠️ OpenTelemetry tracing test failed: {e}")

    # Test metrics if configured
    try:
        from opentelemetry import metrics

        meter = metrics.get_meter(__name__)

        print("📈 Testing OpenTelemetry metrics...")
        counter = meter.create_counter("test_counter", description="A test counter")
        counter.add(1, {"test.label": "test_value"})
        print("✅ Test metric recorded successfully")

    except Exception as e:
        print(f"⚠️ OpenTelemetry metrics test failed: {e}")

    print("✅ Application Insights integration test completed!")
    print("📡 Check your Azure Application Insights dashboard in a few minutes to see the telemetry data.")
    return True


if __name__ == "__main__":
    success = test_application_insights()
    sys.exit(0 if success else 1)
