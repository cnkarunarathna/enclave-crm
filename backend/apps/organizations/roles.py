"""
Single source of truth for role-based access control.

RolePermission enforces this matrix on the server; /auth/me sends the same
matrix (as capabilities) to the UI so the frontend never duplicates it.
"""

from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    STAFF = "STAFF", "Staff"


ALL_ROLES = {Role.ADMIN, Role.MANAGER, Role.STAFF}
ADMIN_OR_MANAGER = {Role.ADMIN, Role.MANAGER}

PERMISSION_MATRIX = {
    "company": {
        "read": ALL_ROLES,
        "create": ADMIN_OR_MANAGER,
        "update": ADMIN_OR_MANAGER,
        "delete": {Role.ADMIN},
    },
    "contact": {
        "read": ALL_ROLES,
        "create": ALL_ROLES,  # Staff's "limited write access"
        "update": ADMIN_OR_MANAGER,
        "delete": {Role.ADMIN},
    },
    "activity_log": {
        "read": ADMIN_OR_MANAGER,
    },
}

# DRF viewset action -> matrix verb. Unknown actions map to nothing and are denied.
ACTION_TO_VERB = {
    "list": "read",
    "retrieve": "read",
    "create": "create",
    "update": "update",
    "partial_update": "update",
    "destroy": "delete",
}


def capabilities_for(role: str) -> dict[str, dict[str, bool]]:
    """{'company': {'read': True, 'create': False, ...}, ...} for the given role."""
    return {
        resource: {verb: role in roles for verb, roles in verbs.items()}
        for resource, verbs in PERMISSION_MATRIX.items()
    }
