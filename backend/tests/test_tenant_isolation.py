"""
An Org B user must never read or change Org A's data, through any endpoint.
Other tenants' records answer 404 (not 403) so their ids are not even confirmed.
"""

import pytest

from apps.activity.models import ActivityLog
from apps.crm.models import Company, Contact

from .factories import make_company, make_contact

pytestmark = pytest.mark.django_db


@pytest.fixture
def org_a_data(admin_a):
    company = make_company(admin_a.organization, name="Acme Secret Co")
    contact = make_contact(company, email="secret@acme.test")
    return {"company": company, "contact": contact}


@pytest.fixture
def client_b(auth_client, admin_b):
    # Admin is the most powerful role: if Admin B is blocked, everyone in B is.
    return auth_client(admin_b)


def test_lists_only_show_own_org(client_b, admin_b, org_a_data):
    make_company(admin_b.organization, name="Blue Sky Co")

    companies = client_b.get("/api/v1/companies/").json()["data"]
    contacts = client_b.get("/api/v1/contacts/").json()["data"]

    assert [c["name"] for c in companies] == ["Blue Sky Co"]
    assert contacts == []


@pytest.mark.parametrize("resource", ["companies", "contacts"])
def test_other_orgs_records_are_not_found(client_b, org_a_data, resource):
    obj = org_a_data["company" if resource == "companies" else "contact"]
    url = f"/api/v1/{resource}/{obj.pk}/"

    assert client_b.get(url).status_code == 404
    assert (
        client_b.patch(url, {"name": "Hacked", "full_name": "Hacked"}, format="json").status_code
        == 404
    )
    assert client_b.put(url, {"name": "Hacked"}, format="json").status_code == 404
    assert client_b.delete(url).status_code == 404


def test_other_orgs_records_are_unchanged_after_attempts(client_b, org_a_data):
    company, contact = org_a_data["company"], org_a_data["contact"]
    client_b.patch(f"/api/v1/companies/{company.pk}/", {"name": "Hacked"}, format="json")
    client_b.delete(f"/api/v1/companies/{company.pk}/")
    client_b.delete(f"/api/v1/contacts/{contact.pk}/")

    company = Company.all_objects.get(pk=company.pk)
    assert company.name == "Acme Secret Co"
    assert not company.is_deleted
    assert not Contact.all_objects.get(pk=contact.pk).is_deleted
    assert not ActivityLog.objects.exists()  # nothing happened, nothing logged


def test_cannot_attach_contact_to_another_orgs_company(client_b, org_a_data):
    res = client_b.post(
        "/api/v1/contacts/",
        {"company": org_a_data["company"].pk, "full_name": "Mole", "email": "mole@b.test"},
        format="json",
    )

    assert res.status_code == 400
    assert res.json()["errors"]["company"] == ["Company not found."]
    assert not Contact.all_objects.filter(email="mole@b.test").exists()


def test_company_filter_with_another_orgs_id_returns_nothing(client_b, org_a_data):
    res = client_b.get("/api/v1/contacts/", {"company": org_a_data["company"].pk})

    assert res.status_code == 200
    assert res.json()["data"] == []


def test_activity_logs_are_scoped(auth_client, admin_a, client_b, org_a_data):
    auth_client(admin_a).patch(
        f"/api/v1/companies/{org_a_data['company'].pk}/", {"name": "Renamed"}, format="json"
    )
    log = ActivityLog.objects.get()

    assert client_b.get("/api/v1/activity-logs/").json()["data"] == []
    assert client_b.get(f"/api/v1/activity-logs/{log.pk}/").status_code == 404


def test_dashboard_is_scoped(client_b, org_a_data):
    data = client_b.get("/api/v1/dashboard/stats/").json()["data"]

    assert data["organization"]["name"] == "Org B"
    assert data["totals"] == {"companies": 0, "contacts": 0}


def test_same_company_name_and_contact_email_allowed_in_both_orgs(auth_client, admin_b, org_a_data):
    client = auth_client(admin_b)

    company = client.post("/api/v1/companies/", {"name": "Acme Secret Co"}, format="json")
    contact = client.post(
        "/api/v1/contacts/",
        {"company": company.json()["data"]["id"], "full_name": "X", "email": "secret@acme.test"},
        format="json",
    )

    assert company.status_code == 201
    assert contact.status_code == 201


def test_stale_org_claim_in_token_fails_safe(auth_client, admin_a, org_b, org_a_data):
    """If a token's org_id disagreed with the user's DB org, results are empty (layers AND-ed)."""
    make_company(org_b, name="Blue Sky Co")
    client = auth_client(admin_a)  # token says Org A
    admin_a.organization = org_b  # user moved to Org B in the database
    admin_a.save()

    res = client.get("/api/v1/companies/")

    # View filter says Org B, ambient (token) filter says Org A: both apply, so nothing.
    # Either layer alone would have returned one company.
    assert res.json()["data"] == []
