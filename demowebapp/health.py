"""
Health check views for the Django application.
Provides endpoints to check application and database health.
"""

import logging
import time

from django.conf import settings
from django.db import OperationalError, connections
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .version import get_cached_version

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint that includes database connectivity.
    Returns HTTP 200 if everything is healthy, HTTP 503 if there are issues.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "checks": {},
    }

    status_code = 200

    # Check database connectivity
    db_status = check_database_health()
    health_status["checks"]["database"] = db_status

    if not db_status["healthy"]:
        health_status["status"] = "unhealthy"
        status_code = 503

    # Check Application Insights
    appinsights_status = check_application_insights_health()
    health_status["checks"]["application_insights"] = appinsights_status

    if not appinsights_status["healthy"]:
        # Don't mark the entire app as unhealthy for monitoring issues
        # but include it in the checks
        logger.warning("Application Insights monitoring is not healthy")

    # Add application info
    health_status["application"] = {"name": "demo-webapp", "version": get_cached_version()}

    return JsonResponse(health_status, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def database_health(request):
    """
    Dedicated database health check endpoint.
    """
    db_status = check_database_health()

    if db_status["healthy"]:
        return JsonResponse(db_status, status=200)
    else:
        return JsonResponse(db_status, status=503)


def check_database_health():
    """
    Check database connectivity and return detailed status.
    """
    start_time = time.time()

    try:
        db_conn = connections["default"]
        db_settings = settings.DATABASES["default"]

        # Test database connection with a simple query
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds

        return {
            "healthy": True,
            "response_time_ms": response_time,
            "database_host": db_settings.get("HOST", "unknown"),
            "database_port": db_settings.get("PORT", "unknown"),
            "database_name": db_settings.get("NAME", "unknown"),
            "message": "Database is responding normally",
        }

    except OperationalError as e:
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)

        db_settings = settings.DATABASES.get("default", {})

        return {
            "healthy": False,
            "response_time_ms": response_time,
            "database_host": db_settings.get("HOST", "unknown"),
            "database_port": db_settings.get("PORT", "unknown"),
            "database_name": db_settings.get("NAME", "unknown"),
            "error": str(e),
            "message": "Database connection failed",
            "troubleshooting": {
                "steps": [
                    f"1. Check if the database server at {db_settings.get('HOST', 'unknown')}:"
                    f"{db_settings.get('PORT', 'unknown')} is running",
                    "2. Verify network connectivity to the database server",
                    "3. Check database server logs for any error messages",
                    "4. Ensure the database is accepting connections",
                    "5. Verify database credentials and permissions",
                ]
            },
        }

    except Exception as e:
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)

        db_settings = settings.DATABASES.get("default", {})

        return {
            "healthy": False,
            "response_time_ms": response_time,
            "database_host": db_settings.get("HOST", "unknown"),
            "database_port": db_settings.get("PORT", "unknown"),
            "database_name": db_settings.get("NAME", "unknown"),
            "error": str(e),
            "message": "Unexpected database error",
            "troubleshooting": {
                "steps": [
                    "1. Check application logs for detailed error information",
                    "2. Verify database configuration in Django settings",
                    "3. Test database connectivity manually",
                    "4. Check if database migrations are up to date",
                ]
            },
        }


def check_application_insights_health():
    """
    Check if Application Insights is properly configured and working.

    Returns:
        dict: Health status of Application Insights integration
    """
    import os

    try:
        # Check if Application Insights is enabled
        is_enabled = getattr(settings, "ENABLE_AZURE_MONITOR", False)

        if not is_enabled:
            return {
                "healthy": False,
                "status": "disabled",
                "message": "Application Insights is disabled",
                "details": {
                    "enable_azure_monitor": is_enabled,
                    "connection_string_set": bool(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")),
                },
            }

        # Check if connection string is available
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            return {
                "healthy": False,
                "status": "misconfigured",
                "message": "Application Insights connection string not set",
                "details": {
                    "enable_azure_monitor": is_enabled,
                    "connection_string_set": False,
                },
            }

        # Test if OpenTelemetry components are accessible
        try:
            from opentelemetry import metrics, trace
            from opentelemetry._logs import get_logger_provider

            tracer_provider = trace.get_tracer_provider()
            meter_provider = metrics.get_meter_provider()
            logger_provider = get_logger_provider()

            return {
                "healthy": True,
                "status": "configured",
                "message": "Application Insights is properly configured",
                "details": {
                    "enable_azure_monitor": is_enabled,
                    "connection_string_set": True,
                    "tracer_provider": str(type(tracer_provider).__name__),
                    "meter_provider": str(type(meter_provider).__name__),
                    "logger_provider": str(type(logger_provider).__name__),
                },
            }

        except Exception as otel_error:
            return {
                "healthy": False,
                "status": "opentelemetry_error",
                "message": f"OpenTelemetry components not accessible: {str(otel_error)}",
                "details": {
                    "enable_azure_monitor": is_enabled,
                    "connection_string_set": True,
                    "error": str(otel_error),
                },
            }

    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "message": f"Application Insights health check failed: {str(e)}",
            "details": {"error": str(e)},
        }
