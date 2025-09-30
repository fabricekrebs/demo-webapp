# Performance-optimized Python runtime
FROM python:3.12-slim

# Accept version as build argument
ARG APP_VERSION=dev-unknown

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security and performance
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set the working directory in the container
WORKDIR /app

# Install system dependencies in one layer to reduce image size
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --compile -r requirements.txt

# Create directories with proper permissions for non-root user
RUN mkdir -p /app/static /app/media

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure proper ownership of directories after copying
RUN chown -R appuser:appuser /app/static /app/media

# Make scripts executable
RUN chmod +x /app/start.sh

# Switch to non-root user
USER appuser

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variables
ENV NAME demo-webapp
ENV APP_VERSION=${APP_VERSION}

# Set the default command to the startup script
CMD ["/app/start.sh"]
