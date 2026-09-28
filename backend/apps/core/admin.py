"""Reusable Django admin mixins. Django admin is a platform (superuser) tool, not a tenant UI."""


class SuperuserOnlyMixin:
    """Only superusers may see or edit these models in Django admin."""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class ReadOnlyAdminMixin(SuperuserOnlyMixin):
    """
    View-only admin. Business data must change through the service layer so every
    write is audited; editing it in admin would bypass the activity log.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
