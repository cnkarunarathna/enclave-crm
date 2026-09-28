"""
Writing audit entries, and building the `changes` payload.

Callers (crm.services) run inside transaction.atomic, so if writing the log
fails, the business change is rolled back too: no unaudited writes.

Building `changes`:
    before = field_values(company, fields)   # before mutating
    ...apply changes, save()...
    changes = diff_values(before, field_values(company, fields))
Values are read *after* saving so a new logo is recorded by its final storage key.
"""

from django.db import models
from django.db.models.fields.files import FieldFile

from .models import ActivityLog


def log_activity(*, user, action, obj, changes=None) -> ActivityLog:
    return ActivityLog.objects.create(**_entry(user, action, obj, changes))


def bulk_log_activity(*, user, action, objs, changes=None) -> list[ActivityLog]:
    """One row per object in a single INSERT (used for cascaded contact deletes)."""
    entries = [ActivityLog(**_entry(user, action, obj, changes)) for obj in objs]
    return ActivityLog.objects.bulk_create(entries)


def field_values(instance, fields) -> dict:
    """{field: JSON-safe value} for the given model fields."""
    return {field: _json_value(getattr(instance, field)) for field in fields}


def diff_values(before: dict, after: dict) -> dict:
    """{field: {"old": ..., "new": ...}} for fields whose value changed."""
    return {
        field: {"old": before.get(field), "new": value}
        for field, value in after.items()
        if before.get(field) != value
    }


def snapshot(instance, fields) -> dict:
    """{field: {"new": ...}} describing a newly created record."""
    return {field: {"new": value} for field, value in field_values(instance, fields).items()}


def _entry(user, action, obj, changes) -> dict:
    # A user may only ever produce log rows for their own organization.
    if obj.organization_id != user.organization_id:
        raise ValueError("Cannot log activity for another organization's object.")
    return {
        "organization_id": obj.organization_id,
        "user": user,
        "user_email": user.email,
        "action": action,
        "model_name": type(obj).__name__,
        "object_id": obj.pk,
        "object_repr": str(obj)[:255],
        "changes": changes or {},
    }


def _json_value(value):
    if isinstance(value, FieldFile):
        return value.name or None  # storage key, never a (signed) URL
    if isinstance(value, models.Model):
        return value.pk
    return value
