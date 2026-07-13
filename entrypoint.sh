#!/bin/sh

echo "Running database migrations..."
python manage.py migrate --noinput
echo "Starting development server..."
python manage.py runserver 0.0.0.0:$API_PORT
