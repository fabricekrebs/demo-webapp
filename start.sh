#!/bin/bash

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Run the Django development server
python manage.py runserver 0.0.0.0:8000