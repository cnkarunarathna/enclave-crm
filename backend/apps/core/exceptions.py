"""
Turns every API error into one shape:
{"success": false, "message": "...", "code": "machine_code", "errors": {...} | null}
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

logger = logging.getLogger(__name__)


class Conflict(exceptions.APIException):
    status_code = 409
    default_detail = "The request conflicts with existing data."
    default_code = "conflict"


# Stable machine codes the frontend can switch on.
ERROR_CODES = [
    (exceptions.ValidationError, "validation_error"),
    (exceptions.NotAuthenticated, "not_authenticated"),
    (exceptions.AuthenticationFailed, "not_authenticated"),  # includes simplejwt InvalidToken
    (exceptions.PermissionDenied, "permission_denied"),
    (exceptions.NotFound, "not_found"),
    (exceptions.Throttled, "throttled"),
    (Conflict, "conflict"),
]


def api_exception_handler(exc, context):
    exc = _to_drf_exception(exc)
    response = exception_handler(exc, context)

    if response is None:
        # Unexpected error: full details go to the log, never to the client.
        logger.error("Unhandled API error", exc_info=exc)
        set_rollback()
        return Response(error_body("An unexpected error occurred.", "server_error"), status=500)

    response.data = error_body(_message_for(exc), _code_for(exc), _field_errors_for(exc))
    return response


def error_body(message, code, errors=None):
    return {"success": False, "message": message, "code": code, "errors": errors}


def _to_drf_exception(exc):
    # Map Django exceptions to DRF ones so every error has a status and detail.
    if isinstance(exc, Http404):
        return exceptions.NotFound()
    if isinstance(exc, DjangoPermissionDenied):
        return exceptions.PermissionDenied()
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "error_dict") else exc.messages
        return exceptions.ValidationError(detail=detail)
    if isinstance(exc, IntegrityError):
        # A DB constraint caught a race that serializer validation could not.
        return Conflict()
    return exc


def _code_for(exc):
    for exc_class, code in ERROR_CODES:
        if isinstance(exc, exc_class):
            return code
    return getattr(exc, "default_code", "error")


def _message_for(exc):
    if isinstance(exc, exceptions.ValidationError):
        return "Validation failed."
    detail = exc.detail
    if isinstance(detail, dict):  # simplejwt puts a nested dict here
        detail = detail.get("detail", "")
    if isinstance(detail, list):
        detail = detail[0] if detail else ""
    return str(detail)


def _field_errors_for(exc):
    if not isinstance(exc, exceptions.ValidationError):
        return None
    if isinstance(exc.detail, dict):
        return exc.detail
    return {"non_field_errors": exc.detail}
