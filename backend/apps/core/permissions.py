from rest_framework.permissions import BasePermission

from apps.organizations.roles import ACTION_TO_VERB, PERMISSION_MATRIX


class RolePermission(BasePermission):
    """
    Checks the user's role against PERMISSION_MATRIX.

    The view declares `permission_resource` (e.g. "company"); the DRF action
    (list, create, destroy...) maps to a verb. Anything unknown is denied.
    The role comes from the database user, not the token, so changes apply at once.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.organization_id):
            return False
        verb = ACTION_TO_VERB.get(getattr(view, "action", None))
        resource = getattr(view, "permission_resource", None)
        allowed_roles = PERMISSION_MATRIX.get(resource, {}).get(verb, set())
        return user.role in allowed_roles


class HasOrganization(BasePermission):
    """For endpoints every role may use (e.g. dashboard), but only as a tenant member."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.organization_id)


class IsSameOrganization(BasePermission):
    """Object-level backstop: querysets are already org-scoped, this double-checks."""

    def has_object_permission(self, request, view, obj):
        return obj.organization_id == request.user.organization_id
