"""
Shared fixtures: two organizations, users for each role, and an authenticated
API client that sends a real JWT (so TenantContextMiddleware is exercised too).
"""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.organizations.models import Organization, User
from apps.organizations.roles import Role
from apps.organizations.tokens import issue_tokens

PASSWORD = "Passw0rd!123"


@pytest.fixture(autouse=True)
def _clear_cache():
    # Throttle counters live in the cache; start every test with a clean slate.
    cache.clear()


@pytest.fixture(autouse=True)
def _media_root(settings, tmp_path):
    # Uploaded files go to a temp dir, never the real media/ folder or S3.
    settings.MEDIA_ROOT = tmp_path / "media"


def make_user(email, organization, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, organization=organization, role=role
    )


@pytest.fixture
def org_a(db):
    return Organization.objects.create(name="Org A", subscription_plan=Organization.Plan.PRO)


@pytest.fixture
def org_b(db):
    return Organization.objects.create(name="Org B")


@pytest.fixture
def admin_a(org_a):
    return make_user("admin@a.test", org_a, Role.ADMIN)


@pytest.fixture
def manager_a(org_a):
    return make_user("manager@a.test", org_a, Role.MANAGER)


@pytest.fixture
def staff_a(org_a):
    return make_user("staff@a.test", org_a, Role.STAFF)


@pytest.fixture
def admin_b(org_b):
    return make_user("admin@b.test", org_b, Role.ADMIN)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client():
    """auth_client(user) -> APIClient with `Authorization: Bearer <access>` set."""

    def _make(user):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user)['access']}")
        return client

    return _make
