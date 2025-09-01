"""
Database health check middleware for Django application.
This middleware checks database connectivity and provides helpful error messages
when the database is unresponsive.
"""

import logging
import time

from django.conf import settings
from django.db import OperationalError, connections
from django.http import HttpResponse, JsonResponse

logger = logging.getLogger(__name__)


class DatabaseHealthCheckMiddleware:
    """
    Middleware to check database health and provide informative error messages
    when the database is unresponsive.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.last_db_check = 0
        self.db_check_interval = 60  # Check database health every 60 seconds
        self.db_healthy = True

    def __call__(self, request):
        # Skip database check for health check endpoints to avoid recursion
        if request.path in ["/health/", "/health", "/healthz/", "/healthz"]:
            return self.get_response(request)

        # Check if we need to verify database health
        current_time = time.time()
        if current_time - self.last_db_check > self.db_check_interval:
            self.check_database_health()
            self.last_db_check = current_time

        # If database is unhealthy and this is an API request, return error immediately
        if not self.db_healthy and (
            request.path.startswith("/api/") or request.headers.get("Accept", "").startswith("application/json")
        ):
            return self.get_database_error_response(request)

        try:
            response = self.get_response(request)
            return response
        except OperationalError as e:
            logger.error(f"Database operational error: {e}")
            self.db_healthy = False
            return self.get_database_error_response(request, str(e))
        except Exception as e:
            if "database" in str(e).lower() or "connection" in str(e).lower():
                logger.error(f"Database connection error: {e}")
                self.db_healthy = False
                return self.get_database_error_response(request, str(e))
            raise

    def check_database_health(self):
        """
        Check if the database is responding within the timeout period.
        """
        try:
            db_conn = connections["default"]
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            if not self.db_healthy:
                logger.info("Database connection restored")
            self.db_healthy = True

        except OperationalError as e:
            if self.db_healthy:
                logger.error(f"Database health check failed: {e}")
            self.db_healthy = False
        except Exception as e:
            if self.db_healthy:
                logger.error(f"Unexpected error during database health check: {e}")
            self.db_healthy = False

    def get_database_error_response(self, request, error_details=None):
        """
        Return an appropriate error response when database is unavailable.
        """
        db_host = getattr(settings, "DATABASES", {}).get("default", {}).get("HOST", "unknown")
        db_port = getattr(settings, "DATABASES", {}).get("default", {}).get("PORT", "unknown")

        error_message = {
            "error": "Database Unavailable",
            "message": "The database server is not responding. Please try again later.",
            "details": {
                "database_host": db_host,
                "database_port": db_port,
                "timeout": "30 seconds",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            },
            "troubleshooting": {
                "steps": [
                    f"1. Check if the database server at {db_host}:{db_port} is running",
                    "2. Verify network connectivity to the database server",
                    "3. Check database server logs for any error messages",
                    "4. Ensure the database is accepting connections",
                    "5. Verify database credentials and permissions",
                ],
                "commands": [
                    f"ping {db_host}",
                    f"telnet {db_host} {db_port}",
                    "kubectl get pods -n <database-namespace>  # if using Kubernetes",
                    "docker ps | grep postgres  # if using Docker",
                ],
            },
        }

        if error_details:
            error_message["technical_details"] = error_details

        # Return JSON response for API requests
        if request.path.startswith("/api/") or request.headers.get("Accept", "").startswith("application/json"):
            return JsonResponse(error_message, status=503)

        # Return HTML response for web requests
        html_content = self.get_html_error_page(error_message)
        return HttpResponse(html_content, status=503, content_type="text/html")

    def get_html_error_page(self, error_data):
        """
        Generate an HTML error page for database connectivity issues.
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Connection Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
                .error-container {{ max-width: 800px; margin: 0 auto; }}
                .error-header {{ background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .error-details {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .troubleshooting {{ background-color: #d1ecf1; color: #0c5460; padding: 20px; border-radius: 5px; }}
                .step {{ margin: 10px 0; }}
                .command {{ font-family: monospace; background-color: #e9ecef; padding: 5px; border-radius: 3px; }}
                pre {{ background-color: #e9ecef; padding: 10px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-header">
                    <h1>🚫 Database Connection Error</h1>
                    <p><strong>{error_data['message']}</strong></p>
                </div>
                
                <div class="error-details">
                    <h2>Connection Details</h2>
                    <ul>
                        <li><strong>Database Host:</strong> {error_data['details']['database_host']}</li>
                        <li><strong>Database Port:</strong> {error_data['details']['database_port']}</li>
                        <li><strong>Connection Timeout:</strong> {error_data['details']['timeout']}</li>
                        <li><strong>Timestamp:</strong> {error_data['details']['timestamp']}</li>
                    </ul>
                </div>
                
                <div class="troubleshooting">
                    <h2>🔧 Troubleshooting Steps</h2>
                    <p>Please check the following to resolve this issue:</p>
                    <ol>
                        {"".join([f'<li class="step">{step}</li>' for step in error_data['troubleshooting']['steps']])}
                    </ol>
                    
                    <h3>Diagnostic Commands</h3>
                    <p>You can run these commands to diagnose the issue:</p>
                    <ul>
                        {"".join([
                            f'<li><code class="command">{cmd}</code></li>'
                            for cmd in error_data['troubleshooting']['commands']
                        ])}
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
