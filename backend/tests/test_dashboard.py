import pytest

from .factories import make_company, make_contact

URL = "/api/v1/dashboard/stats/"

pytestmark = pytest.mark.django_db


@pytest.fixture
def data(admin_a, admin_b):
    org = admin_a.organization
    hotel = make_company(org, name="Sunrise", industry="Hospitality")
    make_company(org, name="Palm", industry="Hospitality")
    make_company(org, name="Blank")  # no industry
    make_company(org, name="Gone", industry="Travel", is_deleted=True)
    make_contact(hotel, email="a@example.com")
    make_contact(hotel, email="b@example.com")
    make_contact(hotel, email="c@example.com", is_deleted=True)
    make_company(admin_b.organization, name="Other org", industry="Travel")


def test_totals_and_industries(auth_client, admin_a, data):
    body = auth_client(admin_a).get(URL).json()["data"]

    assert body["organization"] == {"name": "Org A", "subscription_plan": "PRO"}
    assert body["totals"] == {"companies": 3, "contacts": 2}
    assert body["companies_by_industry"] == [
        {"industry": "Hospitality", "count": 2},
        {"industry": "Unspecified", "count": 1},
    ]


def test_admin_sees_recent_activity(auth_client, admin_a):
    client = auth_client(admin_a)
    for i in range(6):
        client.post("/api/v1/companies/", {"name": f"Co {i}"}, format="json")

    recent = client.get(URL).json()["data"]["recent_activity"]

    assert len(recent) == 5
    assert recent[0]["object_repr"] == "Co 5"  # newest first


def test_staff_gets_no_recent_activity(auth_client, admin_a, staff_a):
    auth_client(admin_a).post("/api/v1/companies/", {"name": "Co"}, format="json")

    res = auth_client(staff_a).get(URL)

    assert res.status_code == 200
    assert res.json()["data"]["recent_activity"] == []


def test_requires_authentication(api_client):
    assert api_client.get(URL).status_code == 401
