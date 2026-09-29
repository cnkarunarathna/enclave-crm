#!/bin/sh
# Container entrypoint: optionally apply migrations, then run the given command
# (gunicorn in prod, runserver in dev).
set -e

if [ "${DJANGO_MIGRATE:-0}" = "1" ]; then
  # Compose waits for a healthy database, but retry anyway in case it is still starting.
  attempt=1
  until python manage.py migrate --noinput; do
    if [ "$attempt" -ge 10 ]; then
      echo "entrypoint: database still unavailable, giving up" >&2
      exit 1
    fi
    echo "entrypoint: database not ready, retrying in 3s ($attempt/10)"
    attempt=$((attempt + 1))
    sleep 3
  done
  # Table for the shared cache (rate limiting) in prod settings; no-op if it exists.
  python manage.py createcachetable
fi

exec "$@"
