#!/bin/bash
sleep 5
echo "Applying migrations"
python manage.py migrate
echo "Creating superuser"
python manage.py createsuperuser --noinput
echo "Setting initial data"
python manage.py loaddata data.json
echo "Running server"
python manage.py runserver 0.0.0.0:8000
