from django.db import models
from django.db.models import Q

from apps.core.models import TenantModel

from .storage import company_logo_upload_to


class Company(TenantModel):
    name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    # Stores only the storage key; the API returns a short-lived presigned URL.
    logo = models.ImageField(
        upload_to=company_logo_upload_to, null=True, blank=True, max_length=255
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "companies"
        indexes = [
            models.Index(
                fields=["organization", "is_deleted", "name"], name="company_org_deleted_name_idx"
            ),
        ]

    def __str__(self):
        return self.name


class Contact(TenantModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="contacts")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)  # digits only, 8-15 (validated in API)
    role = models.CharField(max_length=100, blank=True)  # job title, not an RBAC role

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Email is unique per company among *active* contacts, so a soft-deleted
            # contact does not block re-adding the same email later.
            models.UniqueConstraint(
                fields=["company", "email"],
                condition=Q(is_deleted=False),
                name="uniq_contact_email_per_company_active",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "company", "is_deleted"],
                name="contact_org_company_idx",
            ),
        ]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        # A contact always lives in its company's organization; never trust anything else.
        if self.organization_id != self.company.organization_id:
            raise ValueError("Contact.organization must match its company's organization.")
        super().save(*args, **kwargs)
