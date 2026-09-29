"""Production settings: every secret is required and HTTPS hardening is on."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False

# No default: env() raises ImproperlyConfigured if DJANGO_SECRET_KEY is missing.
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
DATABASES = {"default": env.db("DATABASE_URL")}

# Shared cache for rate-limit counters. The default in-process cache would give
# every gunicorn worker its own counter (3 workers = 3x the login limit).
# The table is created by `createcachetable` in entrypoint.sh; set e.g.
# CACHE_URL=redis://... (plus the redis package) to swap backends without code changes.
CACHES = {"default": env.cache("CACHE_URL", default="dbcache://django_cache")}

# Explicit origins only; an empty list means no cross-origin access.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# HTTPS is terminated by the load balancer / reverse proxy in front of gunicorn.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
# Load balancer / container health probes call over plain HTTP inside the network.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/$"]
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_REFERRER_POLICY = "same-origin"

# Structured (JSON) logs in production unless overridden.
LOGGING["handlers"]["console"]["formatter"] = env("LOG_FORMAT", default="json")  # noqa: F405
