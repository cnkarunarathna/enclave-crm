"""
Managers that scope queries to one organization.

- TenantQuerySet.for_org(): the explicit filter every view must use (primary control).
- OrgScopedManager: additionally applies the ambient org from the ContextVar
  (defense in depth). Fail-open when no org is set, e.g. in the shell or migrations,
  which is why views never rely on it alone.
- TenantManager: OrgScopedManager + hides soft-deleted rows.
"""

from django.db import models

from .tenancy import get_current_org_id


class TenantQuerySet(models.QuerySet):
    def for_org(self, org):
        # Accepts an Organization instance or a plain id.
        return self.filter(organization_id=getattr(org, "pk", org))


class OrgScopedManager(models.Manager.from_queryset(TenantQuerySet)):
    def get_queryset(self):
        qs = super().get_queryset()
        org_id = get_current_org_id()
        return qs.filter(organization_id=org_id) if org_id is not None else qs


class TenantManager(OrgScopedManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
