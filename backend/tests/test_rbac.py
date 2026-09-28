"""
The full role x resource x verb matrix, exercised through the real API.

EXPECTED is written out by hand from PROJECT_PLAN.md §7.2 (not imported from
roles.py), so an accidental change to PERMISSION_MATRIX makes these tests fail.
"""

import pytest

from apps.organizations.roles import PERMISSION_MATRIX

from .factories import make_company, make_contact

ALL = {"ADMIN", "MANAGER", "STAFF"}
EXPECTED = {
    ("company", "read"): ALL,
    ("company", "create"): {"ADMIN", "MANAGER"},
    ("company", "update"): {"ADMIN", "MANAGER"},
    ("company", "delete"): {"ADMIN"},
    ("contact", "read"): ALL,
    ("contact", "create"): ALL,
    ("contact", "update"): {"ADMIN", "MANAGER"},
    ("contact", "delete"): {"ADMIN"},
    ("activity_log", "read"): {"ADMIN", "MANAGER"},
}
SUCCESS_STATUS = {"read": 200, "create": 201, "update": 200, "delete": 200}
USER_FIXTURE = {"ADMIN": "admin_a", "MANAGER": "manager_a", "STAFF": "staff_a"}

pytestmark = pytest.mark.django_db


def call(client, resource, verb, org):
    """Perform `verb` on `resource` and return the response."""
    company = make_company(org, name="Target")
    contact = make_contact(company, email="target@example.com")

    if resource == "company":
        url = f"/api/v1/companies/{company.pk}/"
        requests = {
            "read": lambda: client.get(url),
            "create": lambda: client.post("/api/v1/companies/", {"name": "New"}, format="json"),
            "update": lambda: client.patch(url, {"name": "Renamed"}, format="json"),
            "delete": lambda: client.delete(url),
        }
    elif resource == "contact":
        url = f"/api/v1/contacts/{contact.pk}/"
        new_contact = {"company": company.pk, "full_name": "New", "email": "new@example.com"}
        requests = {
            "read": lambda: client.get(url),
            "create": lambda: client.post("/api/v1/contacts/", new_contact, format="json"),
            "update": lambda: client.patch(url, {"full_name": "Renamed"}, format="json"),
            "delete": lambda: client.delete(url),
        }
    else:
        requests = {"read": lambda: client.get("/api/v1/activity-logs/")}
    return requests[verb]()


@pytest.mark.parametrize("role", sorted(ALL))
@pytest.mark.parametrize(("resource", "verb"), sorted(EXPECTED))
def test_permission_matrix(request, auth_client, role, resource, verb):
    user = request.getfixturevalue(USER_FIXTURE[role])

    res = call(auth_client(user), resource, verb, user.organization)

    if role in EXPECTED[(resource, verb)]:
        assert res.status_code == SUCCESS_STATUS[verb], res.json()
    else:
        assert res.status_code == 403
        assert res.json()["code"] == "permission_denied"


def test_matrix_in_code_matches_the_spec():
    actual = {
        (resource, verb): {str(role) for role in roles}
        for resource, verbs in PERMISSION_MATRIX.items()
        for verb, roles in verbs.items()
    }
    assert actual == EXPECTED


def test_unauthenticated_requests_are_401(api_client):
    for url in ["/api/v1/companies/", "/api/v1/contacts/", "/api/v1/activity-logs/"]:
        assert api_client.get(url).status_code == 401
