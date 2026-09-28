from datetime import timedelta

import pytest
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import AccessToken

from apps.organizations.models import User
from apps.organizations.tokens import issue_tokens

from .conftest import PASSWORD

LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/auth/me/"

pytestmark = pytest.mark.django_db


def login(client, email, password=PASSWORD):
    return client.post(LOGIN, {"email": email, "password": password}, format="json")


# --- Login ------------------------------------------------------------------


def test_login_returns_tokens_and_user(api_client, admin_a):
    res = login(api_client, "admin@a.test")

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert data["access"] and data["refresh"]
    assert data["user"]["email"] == "admin@a.test"
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["organization"]["name"] == "Org A"


def test_access_token_carries_tenant_claims(api_client, manager_a):
    access = login(api_client, "manager@a.test").json()["data"]["access"]
    token = AccessToken(access)

    assert token["org_id"] == manager_a.organization_id
    assert token["role"] == "MANAGER"
    assert token["email"] == "manager@a.test"


def test_login_email_is_case_insensitive(api_client, admin_a):
    assert login(api_client, "  ADMIN@A.test ").status_code == 200


@pytest.mark.parametrize("email", ["admin@a.test", "nobody@a.test"])
def test_login_failure_is_generic(api_client, admin_a, email):
    # Same message for "wrong password" and "no such user": no user enumeration.
    res = login(api_client, email, password="wrong-password")

    assert res.status_code == 401
    assert res.json() == {
        "success": False,
        "message": "Invalid email or password.",
        "code": "not_authenticated",
        "errors": None,
    }


def test_inactive_user_cannot_log_in(api_client, admin_a):
    admin_a.is_active = False
    admin_a.save()

    res = login(api_client, "admin@a.test")

    assert res.status_code == 403
    assert res.json()["code"] == "permission_denied"


def test_user_without_org_cannot_log_in(api_client, db):
    User.objects.create_superuser(email="root@platform.test", password=PASSWORD)

    assert login(api_client, "root@platform.test").status_code == 403


def test_login_is_throttled(api_client, admin_a):
    for _ in range(10):
        login(api_client, "admin@a.test", password="wrong-password")

    res = login(api_client, "admin@a.test")

    assert res.status_code == 429
    assert res.json()["code"] == "throttled"


# --- Refresh & logout -------------------------------------------------------


def test_refresh_rotates_and_blacklists_old_token(api_client, admin_a):
    old_refresh = issue_tokens(admin_a)["refresh"]

    res = api_client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert res.status_code == 200
    new = res.json()["data"]
    assert new["access"] and new["refresh"] != old_refresh
    assert AccessToken(new["access"])["org_id"] == admin_a.organization_id

    reused = api_client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert reused.status_code == 401


def test_logout_blacklists_refresh_token(auth_client, api_client, admin_a):
    refresh = issue_tokens(admin_a)["refresh"]

    res = auth_client(admin_a).post(LOGOUT, {"refresh": refresh}, format="json")
    assert res.status_code == 200
    assert res.json()["message"] == "Logged out."

    after = api_client.post(REFRESH, {"refresh": refresh}, format="json")
    assert after.status_code == 401


def test_logout_rejects_another_users_refresh_token(auth_client, admin_a, admin_b):
    refresh_b = issue_tokens(admin_b)["refresh"]

    res = auth_client(admin_a).post(LOGOUT, {"refresh": refresh_b}, format="json")

    assert res.status_code == 400
    assert "refresh" in res.json()["errors"]


def test_logout_requires_authentication(api_client, admin_a):
    refresh = issue_tokens(admin_a)["refresh"]

    assert api_client.post(LOGOUT, {"refresh": refresh}, format="json").status_code == 401


# --- Me & protected endpoints -----------------------------------------------


def test_me_returns_user_org_and_capabilities(auth_client, staff_a):
    res = auth_client(staff_a).get(ME)

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["email"] == "staff@a.test"
    assert data["organization"] == {
        "id": staff_a.organization_id,
        "name": "Org A",
        "subscription_plan": "PRO",
    }
    caps = data["capabilities"]
    assert caps["contact"]["create"] is True
    assert caps["company"]["create"] is False
    assert caps["activity_log"]["read"] is False


def test_protected_endpoint_without_token_is_401(api_client):
    res = api_client.get(ME)

    assert res.status_code == 401
    assert res.json()["code"] == "not_authenticated"


def test_protected_endpoint_with_expired_token_is_401(api_client, admin_a):
    token = AccessToken.for_user(admin_a)
    token.set_exp(lifetime=timedelta(seconds=-1))
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    res = api_client.get(ME)

    assert res.status_code == 401
    assert res.json()["success"] is False


def test_refresh_token_cannot_be_used_as_access_token(api_client, admin_a):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(admin_a)['refresh']}")

    assert api_client.get(ME).status_code == 401


# --- User model -------------------------------------------------------------


def test_regular_user_requires_an_organization(db):
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="orphan@x.test", password=PASSWORD)


def test_email_is_stored_lowercase(org_a):
    user = User.objects.create_user(email="Mixed@Case.TEST", password=PASSWORD, organization=org_a)

    assert user.email == "mixed@case.test"
