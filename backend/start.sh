#!/bin/sh

export DJANGO_SETTINGS_MODULE=DjangoHW.settings



python3 manage.py makemigrations
python3 manage.py migrate

# Run with uWSGI
# uwsgi --module=DjangoHW.wsgi:application \
#     --env DJANGO_SETTINGS_MODULE=DjangoHW.settings \
#     --master \
#     --http=0.0.0.0:80 \
#     --processes=5 \
#     --harakiri=20 \
#     --max-requests=5000 \
#     --vacuum

daphne -b 0.0.0.0 -p 80 DjangoHW.asgi:application