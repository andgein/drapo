#!/bin/bash
set -e

dockerize -wait tcp://db:5432 -timeout 1m

# Fix permissions
chown www-data:www-data /upload
chown -R root:root /root/.ssh
chmod 0600 /root/.ssh/id_rsa

case "$1" in
"manage.py")

    exec python "$@"
    ;;
"runserver")
    python manage.py migrate --noinput

    exec python manage.py runserver 0.0.0.0:8000
    ;;
"web")
    python manage.py collectstatic --noinput
    python manage.py migrate --noinput

    exec gunicorn drapo.wsgi --config gunicorn.conf.py
    ;;
*)
    exec "$@"
    ;;
esac
