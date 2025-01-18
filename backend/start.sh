#!/bin/sh
python3 manage.py makemigrations board
python3 manage.py migrate

# Run with uWSGI
uwsgi --module=VIIV.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=VIIV.settings \
    --master \
    --http=0.0.0.0:80 \
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum