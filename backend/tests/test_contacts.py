"""Contact API: CRUD, list features and soft delete."""

import pytest

from apps.crm.models import Contact

from .factories import make_company, make_contact

URL = "/api/v1/contacts/"

pytestmark = pytest.mark.django_db


def detail(contact):
    return f"{URL}{contact.pk}/"


def emails(res):
    return [row["email"] for row in res.json()["data"]]


@pytest.fixture
def company(org_a):
    return make_company(org_a, name="Sunrise Hotels")


def test_create_contact(auth_client, staff_a, company):
    payload = {
        "company": company.pk,
        "full_name": "Jane Doe",
        "email": "  Jane@Example.COM ",
        "phone": "077 123 4567",
        "role": "CEO",
    }

    res = auth_client(staff_a).post(URL, payload, format="json")

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["company"] == company.pk
    assert data["company_name"] == "Sunrise Hotels"
    assert data["email"] == "jane@example.com"
    assert data["phone"] == "0771234567"
    contact = Contact.objects.get(pk=data["id"])
    assert contact.organization_id == company.organization_id


def test_company_is_required_on_create(auth_client, staff_a):
    res = auth_client(staff_a).post(URL, {"full_name": "X", "email": "x@x.com"}, format="json")

    assert res.status_code == 400
    assert "company" in res.json()["errors"]


def test_cannot_add_contact_to_a_deleted_company(auth_client, admin_a, company):
    company.is_deleted = True
    company.save()

    res = auth_client(admin_a).post(
        URL, {"company": company.pk, "full_name": "X", "email": "x@x.com"}, format="json"
    )

    assert res.status_code == 400
    assert res.json()["errors"]["company"] == ["Company not found."]


def test_list_filter_search_and_ordering(auth_client, staff_a, company):
    other = make_company(staff_a.organization, name="Other")
    make_contact(company, email="bob@example.com", full_name="Bob", role="Sales Manager")
    make_contact(company, email="amy@example.com", full_name="Amy", role="CEO")
    make_contact(other, email="cat@example.com", full_name="Cat", role="Sales Rep")
    client = auth_client(staff_a)

    assert sorted(emails(client.get(URL, {"company": company.pk}))) == [
        "amy@example.com",
        "bob@example.com",
    ]
    assert sorted(emails(client.get(URL, {"role": "sales"}))) == [
        "bob@example.com",
        "cat@example.com",
    ]
    assert emails(client.get(URL, {"search": "amy"})) == ["amy@example.com"]
    assert emails(client.get(URL, {"ordering": "full_name"})) == [
        "amy@example.com",
        "bob@example.com",
        "cat@example.com",
    ]
    assert client.get(URL).json()["meta"]["count"] == 3


def test_update_contact(auth_client, manager_a, company):
    contact = make_contact(company, full_name="Old")

    res = auth_client(manager_a).patch(detail(contact), {"full_name": "New"}, format="json")

    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "New"


def test_company_cannot_be_changed(auth_client, manager_a, company):
    contact = make_contact(company)
    other = make_company(manager_a.organization, name="Other")

    res = auth_client(manager_a).patch(detail(contact), {"company": other.pk}, format="json")

    assert res.status_code == 400
    assert res.json()["errors"]["company"] == ["Company cannot be changed."]
    contact.refresh_from_db()
    assert contact.company_id == company.pk


def test_full_update_with_same_company_is_allowed(auth_client, manager_a, company):
    contact = make_contact(company)
    payload = {"company": company.pk, "full_name": "Jane D", "email": "jane@example.com"}

    assert auth_client(manager_a).put(detail(contact), payload, format="json").status_code == 200


def test_delete_is_soft(auth_client, admin_a, company):
    contact = make_contact(company)
    client = auth_client(admin_a)

    res = client.delete(detail(contact))

    assert res.status_code == 200
    assert res.json()["message"] == "Contact deleted."
    assert Contact.all_objects.get(pk=contact.pk).is_deleted
    assert client.get(detail(contact)).status_code == 404


def test_email_can_be_reused_after_soft_delete(auth_client, admin_a, company):
    client = auth_client(admin_a)
    contact = make_contact(company, email="jane@example.com")
    client.delete(detail(contact))

    res = client.post(
        URL,
        {"company": company.pk, "full_name": "Jane again", "email": "jane@example.com"},
        format="json",
    )

    assert res.status_code == 201


def test_list_query_count_does_not_grow_with_rows(
    auth_client, staff_a, company, django_assert_max_num_queries
):
    """company_name comes from select_related, not one query per contact."""
    for i in range(10):
        make_contact(company, email=f"c{i}@example.com")
    client = auth_client(staff_a)

    with django_assert_max_num_queries(4):
        client.get(URL)
