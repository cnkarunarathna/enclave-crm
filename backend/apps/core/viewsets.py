from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .permissions import IsSameOrganization, RolePermission


class OrganizationScopedMixin:
    """
    Tenant scoping + RBAC for any viewset.

    get_queryset() always filters by the user's organization. DRF's get_object()
    uses get_queryset(), so another tenant's id simply is not found (404).
    Subclasses set `model` and `permission_resource`.
    """

    permission_classes = [IsAuthenticated, RolePermission, IsSameOrganization]
    permission_resource: str = ""
    model = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            # OpenAPI schema generation runs without a real user; nothing is queried.
            return self.model.objects.none()
        return self.model.objects.for_org(self.request.user.organization_id)


class OrganizationScopedViewSet(OrganizationScopedMixin, viewsets.ModelViewSet):
    """Full CRUD on tenant data (Companies, Contacts)."""

    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]


class OrganizationScopedReadOnlyViewSet(OrganizationScopedMixin, viewsets.ReadOnlyModelViewSet):
    """List + retrieve only (Activity log)."""
