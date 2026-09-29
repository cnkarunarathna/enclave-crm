# syntax=docker/dockerfile:1
# Multi-stage image for the Django API.
#   docker build --target dev .   -> all dependency groups, runserver (docker-compose.yml)
#   docker build .                -> slim, non-root gunicorn image (docker-compose.prod.yml)

ARG PYTHON_IMAGE=python:3.12-slim

# ---- base: Python + uv; the virtualenv lives outside /app so a bind mount can't hide it
FROM ${PYTHON_IMAGE} AS base
COPY --from=ghcr.io/astral-sh/uv:0.9.15 /uv /bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# ---- dev: every dependency group (tests, ruff); source is bind-mounted by compose
FROM base AS dev
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --all-groups
COPY . .
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---- builder: runtime + prod dependencies only, then collect static files
FROM base AS builder
# Dependencies first so this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --group prod
COPY . .
# Throwaway values that only let prod settings load for collectstatic; they are
# scoped to this RUN and not stored in the image. Real ones come from the runtime env.
RUN DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=collectstatic-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite:////tmp/unused.sqlite3 \
    python manage.py collectstatic --noinput

# ---- prod (default): no uv, no build tools, runs as an unprivileged user
FROM ${PYTHON_IMAGE} AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod
RUN groupadd --system app && useradd --system --gid app --home-dir /app app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# Code stays owned by root: the app user can read it but not modify it.
COPY --from=builder /app /app
# The only writable path: local logo storage (USE_S3=False); compose mounts a volume here.
RUN mkdir -p /app/media && chown app:app /app/media
USER app
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
# Tune with GUNICORN_CMD_ARGS, e.g. "--workers 5 --timeout 60". The control socket
# (for gunicorn's admin CLI) is unused and would need a writable /app.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--no-control-socket"]
