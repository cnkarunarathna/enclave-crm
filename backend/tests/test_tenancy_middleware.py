"""TenantContextMiddleware sets the current org from the JWT and always resets it."""

import pytest
from django.test import RequestFactory

from apps.core.middleware import TenantContextMiddleware
from apps.core.tenancy import get_current_org_id
from apps.organizations.tokens import issue_tokens

pytestmark = pytest.mark.django_db


def run_middleware(**headers):
    seen = {}

    def get_response(request):
        seen["org_id"] = get_current_org_id()
        return "response"

    request = RequestFactory().get("/", headers=headers)
    TenantContextMiddleware(get_response)(request)
    return seen["org_id"]


def test_sets_org_from_access_token_and_resets_after(admin_a):
    access = issue_tokens(admin_a)["access"]

    assert run_middleware(Authorization=f"Bearer {access}") == admin_a.organization_id
    assert get_current_org_id() is None  # nothing leaks after the request


def test_no_token_means_no_org():
    assert run_middleware() is None


def test_invalid_token_means_no_org():
    assert run_middleware(Authorization="Bearer not-a-jwt") is None


def test_refresh_token_is_ignored(admin_a):
    refresh = issue_tokens(admin_a)["refresh"]

    assert run_middleware(Authorization=f"Bearer {refresh}") is None


def test_resets_even_when_view_raises(admin_a):
    access = issue_tokens(admin_a)["access"]

    def boom(request):
        raise RuntimeError("view failed")

    request = RequestFactory().get("/", headers={"Authorization": f"Bearer {access}"})
    with pytest.raises(RuntimeError):
        TenantContextMiddleware(boom)(request)

    assert get_current_org_id() is None
