"""Every response uses the same success / error envelope."""

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from rest_framework import exceptions

from apps.core.exceptions import api_exception_handler

pytestmark = pytest.mark.django_db


def handle(exc):
    return api_exception_handler(exc, context={})


def test_success_envelope(auth_client, admin_a):
    body = auth_client(admin_a).get("/api/v1/auth/me/").json()

    assert body["success"] is True
    assert body["message"] == ""
    assert body["data"]["email"] == "admin@a.test"


def test_validation_error_envelope(api_client):
    res = api_client.post("/api/v1/auth/login/", {}, format="json")

    assert res.status_code == 400
    body = res.json()
    assert body["success"] is False
    assert body["message"] == "Validation failed."
    assert body["code"] == "validation_error"
    assert set(body["errors"]) == {"email", "password"}


def test_health_is_public(api_client):
    res = api_client.get("/api/v1/health/")

    assert res.status_code == 200
    assert res.json() == {"success": True, "message": "", "data": {"status": "ok"}}


def test_not_found_envelope():
    res = handle(Http404())

    assert res.status_code == 404
    assert res.data == {
        "success": False,
        "message": "Not found.",
        "code": "not_found",
        "errors": None,
    }


def test_permission_denied_envelope():
    res = handle(exceptions.PermissionDenied())

    assert res.status_code == 403
    assert res.data["code"] == "permission_denied"


def test_integrity_error_becomes_409():
    res = handle(IntegrityError("duplicate key value violates unique constraint"))

    assert res.status_code == 409
    assert res.data["code"] == "conflict"
    assert "duplicate key" not in res.data["message"]


def test_django_validation_error_becomes_400():
    res = handle(DjangoValidationError({"email": ["Bad email."]}))

    assert res.status_code == 400
    assert res.data["errors"] == {"email": ["Bad email."]}


def test_unexpected_error_hides_internals():
    res = handle(RuntimeError("secret connection string leaked"))

    assert res.status_code == 500
    assert res.data == {
        "success": False,
        "message": "An unexpected error occurred.",
        "code": "server_error",
        "errors": None,
    }
