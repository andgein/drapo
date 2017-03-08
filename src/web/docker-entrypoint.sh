#!/bin/bash
set -e

dockerize -wait tcp://db:5432 -timeout 1m

case "$1" in
"manage.py")

    exec python "$@"
    ;;
"runserver")
    python manage.py migrate --noinput

    exec python manage.py runserver 0.0.0.0:8000
    ;;
"web")
    #python manage.py collectstatic --noinput
    python manage.py migrate --noinput

    exec gunicorn drapo.wsgi --config gunicorn.conf.py
    ;;
*)
    exec "$@"
    ;;
esac
