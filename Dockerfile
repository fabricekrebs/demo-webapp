# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make the startup script executable
RUN chmod +x /app/start.sh && apt-get update && apt-get install -y \
    libpq-dev \
    python3-dev \
    python3-psycopg2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME demo-webapp

# Set the entry point to the startup script
ENTRYPOINT ["/app/start.sh"]
