"""Production-readiness details: API docs, rate-limit spoofing, structured logs."""

import json
import logging

import pytest

from apps.core.log_formatters import JsonFormatter

from .factories import PASSWORD

pytestmark = pytest.mark.django_db


def test_openapi_schema_and_swagger_render(api_client):
    schema = api_client.get("/api/v1/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
    docs = api_client.get("/api/v1/docs/")

    assert schema.status_code == 200
    assert "/api/v1/companies/" in schema.json()["paths"]
    assert docs.status_code == 200
    assert b"swagger" in docs.content.lower()


def test_login_throttle_cannot_be_bypassed_with_x_forwarded_for(api_client, admin_a):
    # Each attempt claims to come from a different IP; the limit must still apply.
    for i in range(10):
        api_client.post(
            "/api/v1/auth/login/",
            {"email": "admin@a.test", "password": "wrong"},
            format="json",
            HTTP_X_FORWARDED_FOR=f"203.0.113.{i}",
        )

    res = api_client.post(
        "/api/v1/auth/login/",
        {"email": "admin@a.test", "password": PASSWORD},
        format="json",
        HTTP_X_FORWARDED_FOR="203.0.113.99",
    )

    assert res.status_code == 429


def test_json_log_formatter():
    record = logging.LogRecord(
        "django.request", logging.ERROR, __file__, 1, "Boom %s", ("x",), None
    )
    record.status_code = 500

    entry = json.loads(JsonFormatter().format(record))

    assert entry["level"] == "ERROR"
    assert entry["logger"] == "django.request"
    assert entry["message"] == "Boom x"
    assert entry["status_code"] == 500
    assert entry["time"].endswith("+00:00")
