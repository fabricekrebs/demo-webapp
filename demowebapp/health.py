"""
Health check views for the Django application.
Provides endpoints to check application and database health.
"""
import time
import logging
from django.http import JsonResponse
from django.db import connections, OperationalError
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

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
        "checks": {}
    }
    
    status_code = 200
    
    # Check database connectivity
    db_status = check_database_health()
    health_status["checks"]["database"] = db_status
    
    if not db_status["healthy"]:
        health_status["status"] = "unhealthy"
        status_code = 503
    
    # Add application info
    health_status["application"] = {
        "name": "demo-webapp",
        "version": "1.0.0"
    }
    
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
        db_conn = connections['default']
        db_settings = settings.DATABASES['default']
        
        # Test database connection with a simple query
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        return {
            "healthy": True,
            "response_time_ms": response_time,
            "database_host": db_settings.get('HOST', 'unknown'),
            "database_port": db_settings.get('PORT', 'unknown'),
            "database_name": db_settings.get('NAME', 'unknown'),
            "message": "Database is responding normally"
        }
        
    except OperationalError as e:
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        db_settings = settings.DATABASES.get('default', {})
        
        return {
            "healthy": False,
            "response_time_ms": response_time,
            "database_host": db_settings.get('HOST', 'unknown'),
            "database_port": db_settings.get('PORT', 'unknown'),
            "database_name": db_settings.get('NAME', 'unknown'),
            "error": str(e),
            "message": "Database connection failed",
            "troubleshooting": {
                "steps": [
                    f"1. Check if the database server at {db_settings.get('HOST', 'unknown')}:{db_settings.get('PORT', 'unknown')} is running",
                    "2. Verify network connectivity to the database server",
                    "3. Check database server logs for any error messages",
                    "4. Ensure the database is accepting connections",
                    "5. Verify database credentials and permissions"
                ]
            }
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        db_settings = settings.DATABASES.get('default', {})
        
        return {
            "healthy": False,
            "response_time_ms": response_time,
            "database_host": db_settings.get('HOST', 'unknown'),
            "database_port": db_settings.get('PORT', 'unknown'),
            "database_name": db_settings.get('NAME', 'unknown'),
            "error": str(e),
            "message": "Unexpected database error",
            "troubleshooting": {
                "steps": [
                    "1. Check application logs for detailed error information",
                    "2. Verify database configuration in Django settings",
                    "3. Test database connectivity manually",
                    "4. Check if database migrations are up to date"
                ]
            }
        }
