"""Company API: CRUD, list features, logos and soft delete."""

import pytest
from django.core.files.storage import default_storage

from apps.crm.models import Company, Contact

from .factories import make_company, make_contact, make_image

URL = "/api/v1/companies/"

pytestmark = pytest.mark.django_db


def detail(company):
    return f"{URL}{company.pk}/"


def names(res):
    return [row["name"] for row in res.json()["data"]]


# --- Create ------------------------------------------------------------------


def test_create_company(auth_client, manager_a):
    payload = {"name": "Sunrise Hotels", "industry": "Hospitality", "country": "Sri Lanka"}

    res = auth_client(manager_a).post(URL, payload, format="json")

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["name"] == "Sunrise Hotels"
    assert data["logo_url"] is None
    assert data["contacts_count"] == 0
    assert "organization" not in data
    assert Company.objects.get(pk=data["id"]).organization_id == manager_a.organization_id


def test_server_sets_organization_and_ignores_client_values(auth_client, admin_a, org_b):
    payload = {"name": "Sneaky", "organization": org_b.pk, "is_deleted": True}

    res = auth_client(admin_a).post(URL, payload, format="json")

    company = Company.all_objects.get(pk=res.json()["data"]["id"])
    assert company.organization_id == admin_a.organization_id
    assert company.is_deleted is False


def test_name_is_required(auth_client, admin_a):
    res = auth_client(admin_a).post(URL, {"industry": "Tech"}, format="json")

    assert res.status_code == 400
    assert "name" in res.json()["errors"]


def test_create_with_logo_stores_it_under_the_org_prefix(auth_client, admin_a):
    res = auth_client(admin_a).post(
        URL, {"name": "Logo Co", "logo": make_image()}, format="multipart"
    )

    assert res.status_code == 201
    company = Company.objects.get(pk=res.json()["data"]["id"])
    assert company.logo.name.startswith(f"org-{admin_a.organization_id}/logos/")
    assert default_storage.exists(company.logo.name)
    assert res.json()["data"]["logo_url"].endswith(company.logo.name)


# --- List, search, filter, order ---------------------------------------------


def test_list_is_paginated(auth_client, staff_a):
    for i in range(13):
        make_company(staff_a.organization, name=f"Company {i:02}")

    res = auth_client(staff_a).get(URL, {"page": 2})

    body = res.json()
    assert res.status_code == 200
    assert body["meta"] == {"count": 13, "page": 2, "page_size": 10, "total_pages": 2}
    assert len(body["data"]) == 3


def test_page_size_can_be_changed(auth_client, staff_a):
    for i in range(3):
        make_company(staff_a.organization, name=f"Company {i}")

    res = auth_client(staff_a).get(URL, {"page_size": 2})

    assert res.json()["meta"]["total_pages"] == 2


def test_search_filter_and_ordering(auth_client, staff_a):
    org = staff_a.organization
    make_company(org, name="Sunrise Hotels", industry="Hospitality", country="Sri Lanka")
    make_company(org, name="Sunset Tours", industry="Travel", country="India")
    make_company(org, name="Acme Tech", industry="Technology", country="Sri Lanka")
    client = auth_client(staff_a)

    assert sorted(names(client.get(URL, {"search": "sun"}))) == ["Sunrise Hotels", "Sunset Tours"]
    assert names(client.get(URL, {"industry": "travel"})) == ["Sunset Tours"]  # iexact
    assert sorted(names(client.get(URL, {"country": "sri lanka"}))) == [
        "Acme Tech",
        "Sunrise Hotels",
    ]
    assert names(client.get(URL, {"ordering": "name"})) == [
        "Acme Tech",
        "Sunrise Hotels",
        "Sunset Tours",
    ]


def test_contacts_count_ignores_deleted_contacts(auth_client, staff_a):
    company = make_company(staff_a.organization)
    make_contact(company, email="a@example.com")
    make_contact(company, email="b@example.com")
    make_contact(company, email="c@example.com", is_deleted=True)

    res = auth_client(staff_a).get(detail(company))

    assert res.json()["data"]["contacts_count"] == 2


# --- Update ------------------------------------------------------------------


def test_partial_update(auth_client, manager_a):
    company = make_company(manager_a.organization, name="Old name", industry="Tech")

    res = auth_client(manager_a).patch(detail(company), {"name": "New name"}, format="json")

    assert res.status_code == 200
    assert res.json()["data"]["name"] == "New name"
    assert res.json()["data"]["industry"] == "Tech"


def test_replacing_a_logo_deletes_the_old_file_after_commit(
    auth_client, admin_a, django_capture_on_commit_callbacks
):
    client = auth_client(admin_a)
    company_id = client.post(URL, {"name": "Logo Co", "logo": make_image()}, format="multipart")
    company = Company.objects.get(pk=company_id.json()["data"]["id"])
    old_key = company.logo.name

    with django_capture_on_commit_callbacks(execute=True):
        res = client.patch(detail(company), {"logo": make_image("new.png")}, format="multipart")

    company.refresh_from_db()
    assert res.status_code == 200
    assert company.logo.name != old_key
    assert default_storage.exists(company.logo.name)
    assert not default_storage.exists(old_key)


def test_remove_logo(auth_client, admin_a, django_capture_on_commit_callbacks):
    client = auth_client(admin_a)
    created = client.post(URL, {"name": "Logo Co", "logo": make_image()}, format="multipart")
    company = Company.objects.get(pk=created.json()["data"]["id"])
    old_key = company.logo.name

    with django_capture_on_commit_callbacks(execute=True):
        res = client.patch(detail(company), {"remove_logo": True}, format="json")

    assert res.json()["data"]["logo_url"] is None
    assert not default_storage.exists(old_key)


def test_logo_and_remove_logo_together_is_rejected(auth_client, admin_a):
    company = make_company(admin_a.organization)

    res = auth_client(admin_a).patch(
        detail(company), {"logo": make_image(), "remove_logo": "true"}, format="multipart"
    )

    assert res.status_code == 400
    assert "remove_logo" in res.json()["errors"]


# --- Soft delete -------------------------------------------------------------


def test_delete_is_soft_and_cascades_to_contacts(auth_client, admin_a):
    company = make_company(admin_a.organization)
    contact = make_contact(company)
    client = auth_client(admin_a)

    res = client.delete(detail(company))

    assert res.status_code == 200
    assert res.json() == {"success": True, "message": "Company deleted.", "data": None}
    # Rows still exist, flagged as deleted...
    assert Company.all_objects.get(pk=company.pk).is_deleted
    assert Company.all_objects.get(pk=company.pk).deleted_at is not None
    assert Contact.all_objects.get(pk=contact.pk).is_deleted
    # ...but are gone from the API.
    assert client.get(detail(company)).status_code == 404
    assert client.get(URL).json()["meta"]["count"] == 0
    assert client.get("/api/v1/contacts/").json()["meta"]["count"] == 0


def test_deleted_company_keeps_its_logo_file(auth_client, admin_a):
    client = auth_client(admin_a)
    created = client.post(URL, {"name": "Logo Co", "logo": make_image()}, format="multipart")
    company = Company.objects.get(pk=created.json()["data"]["id"])

    client.delete(detail(company))

    assert default_storage.exists(company.logo.name)


# --- Performance -------------------------------------------------------------


def test_list_query_count_does_not_grow_with_rows(
    auth_client, staff_a, django_assert_max_num_queries
):
    """contacts_count is annotated, so 10 rows cost the same as 1 (no N+1)."""
    for i in range(10):
        make_contact(make_company(staff_a.organization, name=f"Co {i}"), email=f"c{i}@example.com")
    client = auth_client(staff_a)

    # auth user + count + page (+ savepoint noise); never one query per row.
    with django_assert_max_num_queries(4):
        client.get(URL)
