from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from apps.core.managers import OrgScopedManager


class ActivityLog(models.Model):
    """
    Append-only audit trail of every create/update/delete on Companies and Contacts.

    Rows are written only by activity.services, inside the same transaction as
    the change they describe. There are no update or delete endpoints.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"

    class ModelName(models.TextChoices):
        COMPANY = "Company", "Company"
        CONTACT = "Contact", "Contact"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="+",
        db_index=True,
    )
    # SET_NULL + email snapshot: the log stays readable if the user is removed.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    user_email = models.EmailField(blank=True)
    action = models.CharField(max_length=10, choices=Action.choices)
    model_name = models.CharField(max_length=50, choices=ModelName.choices)
    object_id = models.PositiveBigIntegerField()
    object_repr = models.CharField(max_length=255)
    # {field: {"old": ..., "new": ...}}. Files are stored as storage keys, never URLs.
    changes = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Ambient org filter; no soft delete (the log is never deleted).
    objects = OrgScopedManager()
    all_objects = models.Manager()  # noqa: DJ012 (ruff mistakes a manager for a field)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["organization", "-timestamp"], name="activity_org_time_idx"),
            models.Index(
                fields=["organization", "model_name", "object_id"], name="activity_org_object_idx"
            ),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id} by {self.user_email}"

    def save(self, *args, **kwargs):
        # Immutable: a log entry can be created but never edited.
        if not self._state.adding:
            raise ValueError("Activity log entries are immutable.")
        super().save(*args, **kwargs)
