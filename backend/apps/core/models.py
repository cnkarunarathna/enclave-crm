from django.db import models

from .managers import TenantManager


class TenantModel(models.Model):
    """
    Base for every record owned by an organization (Company, Contact).

    `organization` is always set by the server (service layer), never from client input.
    DELETE is a soft delete: rows are flagged, not removed.
    """

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="+",  # no reverse accessor; always query through the model
        db_index=True,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Default manager: ambient org filter + hides soft-deleted rows.
    objects = TenantManager()
    # Unfiltered escape hatch for tests, admin and services that need deleted rows.
    all_objects = models.Manager()  # noqa: DJ012 (ruff mistakes a manager for a field)

    class Meta:
        abstract = True
