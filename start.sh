#!/bin/bash

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Run the Django development server
gunicorn demowebapp.wsgi --bind 0.0.0.0:8000 --workers 4