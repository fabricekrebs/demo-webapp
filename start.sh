#!/bin/bash

# Performance-optimized startup script
echo "🚀 Starting demo-webapp with performance optimizations..."

# Calculate optimal worker count based on container resources
WORKERS=${GUNICORN_WORKERS:-2}
WORKER_CLASS=${GUNICORN_WORKER_CLASS:-sync}
WORKER_CONNECTIONS=${GUNICORN_WORKER_CONNECTIONS:-1000}
MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-100}
# Increase timeout to handle Azure AI calls better (while async processing handles long operations)
TIMEOUT=${GUNICORN_TIMEOUT:-60}
KEEPALIVE=${GUNICORN_KEEPALIVE:-2}

echo "📊 Performance Settings:"
echo "   Workers: $WORKERS"
echo "   Worker Class: $WORKER_CLASS"
echo "   Max Requests: $MAX_REQUESTS (with jitter: $MAX_REQUESTS_JITTER)"
echo "   Timeout: ${TIMEOUT}s"
echo "   Keep-Alive: ${KEEPALIVE}s"

# Run database migrations (only if needed)
if [ "$SKIP_MIGRATIONS" != "true" ]; then
    echo "🗄️  Running database migrations..."
    python manage.py migrate --noinput
else
    echo "⏭️  Skipping migrations (SKIP_MIGRATIONS=true)"
fi

# Collect static files in production
if [ "$DJANGO_SETTINGS_MODULE" != "demowebapp.test_settings" ] && [ "$COLLECT_STATIC" != "false" ]; then
    echo "📁 Collecting static files..."
    
    # Ensure static directory exists and has proper permissions
    mkdir -p /app/static /app/media
    
    python manage.py collectstatic --noinput --clear
fi

echo "🌐 Starting Gunicorn server..."

# Start Gunicorn with optimized settings
exec gunicorn demowebapp.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --worker-class $WORKER_CLASS \
    --worker-connections $WORKER_CONNECTIONS \
    --max-requests $MAX_REQUESTS \
    --max-requests-jitter $MAX_REQUESTS_JITTER \
    --timeout $TIMEOUT \
    --keep-alive $KEEPALIVE \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info