"""Activity log: service helpers, immutability, and the read-only API."""

import pytest

from apps.activity.models import ActivityLog
from apps.activity.services import (
    bulk_log_activity,
    diff_values,
    field_values,
    log_activity,
    snapshot,
)
from apps.crm.models import Company

from .factories import make_company, make_contact, make_image

URL = "/api/v1/activity-logs/"
Action = ActivityLog.Action

pytestmark = pytest.mark.django_db


# --- Services ---------------------------------------------------------------


def test_log_activity_records_who_did_what(admin_a):
    company = make_company(admin_a.organization, name="Sunrise Hotels")

    entry = log_activity(user=admin_a, action=Action.CREATE, obj=company, changes={"a": 1})

    assert entry.organization_id == admin_a.organization_id
    assert entry.user == admin_a
    assert entry.user_email == "admin@a.test"
    assert entry.action == "CREATE"
    assert entry.model_name == "Company"
    assert entry.object_id == company.pk
    assert entry.object_repr == "Sunrise Hotels"
    assert entry.changes == {"a": 1}
    assert entry.timestamp is not None


def test_bulk_log_activity_writes_one_row_per_object(admin_a):
    company = make_company(admin_a.organization)
    contacts = [make_contact(company, email=f"c{i}@example.com") for i in range(3)]

    bulk_log_activity(user=admin_a, action=Action.DELETE, objs=contacts)

    rows = ActivityLog.objects.filter(model_name="Contact", action="DELETE")
    assert sorted(rows.values_list("object_id", flat=True)) == sorted(c.pk for c in contacts)


def test_cannot_log_activity_for_another_organizations_object(admin_a, org_b):
    other_company = make_company(org_b)

    with pytest.raises(ValueError):
        log_activity(user=admin_a, action=Action.UPDATE, obj=other_company)


def test_log_entries_are_immutable(admin_a):
    company = make_company(admin_a.organization)
    entry = log_activity(user=admin_a, action=Action.CREATE, obj=company)
    entry.action = Action.DELETE

    with pytest.raises(ValueError):
        entry.save()


def test_change_helpers(org_a):
    company = make_company(org_a, name="Old", industry="Tech")
    before = field_values(company, ["name", "industry", "logo"])

    company.name = "New"

    assert before == {"name": "Old", "industry": "Tech", "logo": None}
    assert diff_values(before, field_values(company, ["name", "industry", "logo"])) == {
        "name": {"old": "Old", "new": "New"}
    }
    assert snapshot(company, ["name"]) == {"name": {"new": "New"}}


# --- API --------------------------------------------------------------------


@pytest.fixture
def logs(admin_a, admin_b):
    """Two entries in Org A, one in Org B."""
    company_a = make_company(admin_a.organization, name="Alpha")
    contact_a = make_contact(company_a)
    company_b = make_company(admin_b.organization, name="Bravo")
    return {
        "a_company": log_activity(user=admin_a, action=Action.CREATE, obj=company_a),
        "a_contact": log_activity(user=admin_a, action=Action.UPDATE, obj=contact_a),
        "b_company": log_activity(user=admin_b, action=Action.CREATE, obj=company_b),
    }


@pytest.mark.parametrize("user_fixture", ["admin_a", "manager_a"])
def test_admin_and_manager_can_list_own_org_logs(request, auth_client, logs, user_fixture):
    user = request.getfixturevalue(user_fixture)

    res = auth_client(user).get(URL)

    assert res.status_code == 200
    body = res.json()
    ids = {row["id"] for row in body["data"]}
    assert ids == {logs["a_company"].pk, logs["a_contact"].pk}
    assert body["meta"]["count"] == 2


def test_log_row_shape(auth_client, admin_a, logs):
    row = auth_client(admin_a).get(f"{URL}{logs['a_company'].pk}/").json()["data"]

    assert row["user"] == {"id": admin_a.pk, "email": "admin@a.test", "full_name": "admin@a.test"}
    assert row["action"] == "CREATE"
    assert row["model_name"] == "Company"
    assert row["object_repr"] == "Alpha"


def test_staff_cannot_read_logs(auth_client, staff_a, logs):
    assert auth_client(staff_a).get(URL).status_code == 403


def test_other_orgs_log_is_not_found(auth_client, admin_a, logs):
    res = auth_client(admin_a).get(f"{URL}{logs['b_company'].pk}/")

    assert res.status_code == 404
    assert res.json()["code"] == "not_found"


def test_filters_by_model_and_action(auth_client, admin_a, logs):
    res = auth_client(admin_a).get(URL, {"model_name": "Contact", "action": "UPDATE"})

    assert [row["id"] for row in res.json()["data"]] == [logs["a_contact"].pk]


def test_search_by_object_repr(auth_client, admin_a, logs):
    res = auth_client(admin_a).get(URL, {"search": "alph"})

    assert [row["id"] for row in res.json()["data"]] == [logs["a_company"].pk]


def test_log_is_read_only_over_the_api(auth_client, admin_a, logs):
    client = auth_client(admin_a)
    detail = f"{URL}{logs['a_company'].pk}/"

    # Write methods have no viewset action, so RolePermission denies them (deny by default)
    # before DRF would even answer 405. Either way, nothing changes.
    assert client.post(URL, {}, format="json").status_code == 403
    assert client.patch(detail, {"action": "DELETE"}, format="json").status_code == 403
    assert client.delete(detail).status_code == 403
    assert ActivityLog.objects.count() == 3


# --- Every write endpoint is audited -----------------------------------------


def only_log():
    assert ActivityLog.objects.count() == 1
    return ActivityLog.objects.get()


def test_company_create_update_delete_are_logged(auth_client, admin_a):
    client = auth_client(admin_a)

    created = client.post("/api/v1/companies/", {"name": "Acme", "industry": "Tech"}, format="json")
    company_id = created.json()["data"]["id"]
    entry = only_log()
    assert (entry.action, entry.model_name, entry.object_id) == ("CREATE", "Company", company_id)
    assert entry.user == admin_a
    assert entry.changes["name"] == {"new": "Acme"}
    ActivityLog.objects.all().delete()

    client.patch(f"/api/v1/companies/{company_id}/", {"name": "Acme Ltd"}, format="json")
    entry = only_log()
    assert entry.action == "UPDATE"
    assert entry.changes == {"name": {"old": "Acme", "new": "Acme Ltd"}}
    ActivityLog.objects.all().delete()

    client.delete(f"/api/v1/companies/{company_id}/")
    entry = only_log()
    assert (entry.action, entry.object_repr) == ("DELETE", "Acme Ltd")


def test_contact_create_update_delete_are_logged(auth_client, admin_a):
    client = auth_client(admin_a)
    company = make_company(admin_a.organization)

    created = client.post(
        "/api/v1/contacts/",
        {"company": company.pk, "full_name": "Jane", "email": "jane@example.com"},
        format="json",
    )
    contact_id = created.json()["data"]["id"]
    entry = only_log()
    assert (entry.action, entry.model_name, entry.object_id) == ("CREATE", "Contact", contact_id)
    assert entry.changes["company"] == {"new": company.pk}
    ActivityLog.objects.all().delete()

    client.patch(f"/api/v1/contacts/{contact_id}/", {"phone": "12345678"}, format="json")
    assert only_log().changes == {"phone": {"old": "", "new": "12345678"}}
    ActivityLog.objects.all().delete()

    client.delete(f"/api/v1/contacts/{contact_id}/")
    assert only_log().action == "DELETE"


def test_company_delete_logs_each_cascaded_contact(auth_client, admin_a):
    company = make_company(admin_a.organization)
    contacts = [make_contact(company, email=f"c{i}@example.com") for i in range(3)]
    make_contact(company, email="old@example.com", is_deleted=True)  # already gone: not logged

    auth_client(admin_a).delete(f"/api/v1/companies/{company.pk}/")

    deletes = ActivityLog.objects.filter(action="DELETE")
    assert deletes.count() == 4
    assert deletes.filter(model_name="Company", object_id=company.pk).count() == 1
    assert sorted(
        deletes.filter(model_name="Contact").values_list("object_id", flat=True)
    ) == sorted(c.pk for c in contacts)


def test_logo_change_is_logged_as_storage_key(auth_client, admin_a):
    res = auth_client(admin_a).post(
        "/api/v1/companies/", {"name": "Logo Co", "logo": make_image()}, format="multipart"
    )
    logged_logo = only_log().changes["logo"]["new"]

    assert logged_logo.startswith(f"org-{admin_a.organization_id}/logos/")
    assert "X-Amz" not in logged_logo and "http" not in logged_logo
    assert res.status_code == 201


def test_failed_log_write_rolls_back_the_change(auth_client, admin_a, monkeypatch):
    def broken_log(**kwargs):
        raise RuntimeError("audit store down")

    monkeypatch.setattr("apps.crm.services.log_activity", broken_log)

    res = auth_client(admin_a).post("/api/v1/companies/", {"name": "Unaudited"}, format="json")

    assert res.status_code == 500
    assert "audit store" not in res.json()["message"]
    assert not Company.all_objects.filter(name="Unaudited").exists()


def test_rejected_writes_are_not_logged(auth_client, staff_a, admin_a):
    auth_client(staff_a).post("/api/v1/companies/", {"name": "Nope"}, format="json")  # 403
    auth_client(admin_a).post("/api/v1/companies/", {}, format="json")  # 400

    assert not ActivityLog.objects.exists()


def test_list_query_count_does_not_grow_with_rows(
    auth_client, admin_a, django_assert_max_num_queries
):
    company = make_company(admin_a.organization)
    for _ in range(10):
        log_activity(user=admin_a, action=Action.UPDATE, obj=company)
    client = auth_client(admin_a)

    with django_assert_max_num_queries(4):
        client.get(URL)
