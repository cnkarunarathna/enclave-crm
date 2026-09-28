"""Company/Contact models: DB constraints, soft-delete managers and logo storage keys."""

import pytest
from django.db import IntegrityError, transaction

from apps.core.tenancy import reset_current_org_id, set_current_org_id
from apps.crm.models import Company, Contact
from apps.crm.storage import company_logo_upload_to

from .factories import make_company, make_contact

pytestmark = pytest.mark.django_db


# --- Contact email uniqueness (partial unique index) ------------------------


def test_duplicate_active_email_in_same_company_is_rejected(org_a):
    company = make_company(org_a)
    make_contact(company, email="jane@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_contact(company, email="jane@example.com")


def test_email_uniqueness_ignores_case(org_a):
    company = make_company(org_a)
    make_contact(company, email="jane@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_contact(company, email=" JANE@Example.com ")


def test_same_email_allowed_in_different_companies(org_a):
    make_contact(make_company(org_a, name="One"), email="jane@example.com")

    make_contact(make_company(org_a, name="Two"), email="jane@example.com")

    assert Contact.objects.filter(email="jane@example.com").count() == 2


def test_soft_deleted_contact_frees_its_email(org_a):
    company = make_company(org_a)
    old = make_contact(company, email="jane@example.com")
    old.is_deleted = True
    old.save()

    make_contact(company, email="jane@example.com")

    assert Contact.all_objects.filter(email="jane@example.com").count() == 2


def test_contact_must_share_its_companys_organization(org_a, org_b):
    company_a = make_company(org_a)

    with pytest.raises(ValueError):
        Contact.objects.create(
            organization=org_b, company=company_a, full_name="X", email="x@example.com"
        )


# --- Managers ---------------------------------------------------------------


def test_default_manager_hides_soft_deleted_rows(org_a):
    make_company(org_a, name="Active")
    make_company(org_a, name="Deleted", is_deleted=True)

    assert list(Company.objects.values_list("name", flat=True)) == ["Active"]
    assert Company.all_objects.count() == 2


def test_for_org_filters_by_organization(org_a, org_b):
    make_company(org_a, name="A co")
    make_company(org_b, name="B co")

    assert list(Company.objects.for_org(org_a).values_list("name", flat=True)) == ["A co"]
    assert list(Company.objects.for_org(org_b.pk).values_list("name", flat=True)) == ["B co"]


def test_ambient_org_filter_applies_when_set(org_a, org_b):
    make_company(org_a, name="A co")
    make_company(org_b, name="B co")

    token = set_current_org_id(org_b.pk)
    try:
        assert list(Company.objects.values_list("name", flat=True)) == ["B co"]
        # Explicit for_org() is AND-ed with the ambient filter: a mismatch yields nothing.
        assert not Company.objects.for_org(org_a).exists()
    finally:
        reset_current_org_id(token)

    # Unset (shell, migrations): no ambient filter, so views must always use for_org().
    assert Company.objects.count() == 2


def test_company_contacts_relation_hides_deleted_contacts(org_a):
    company = make_company(org_a)
    make_contact(company, email="a@example.com")
    make_contact(company, email="b@example.com", is_deleted=True)

    assert company.contacts.count() == 1


# --- Logo storage keys ------------------------------------------------------


def test_logo_key_is_namespaced_by_org_and_randomized(org_a):
    company = Company(organization=org_a, name="X")

    key = company_logo_upload_to(company, "My Logo.PNG")

    assert key.startswith(f"org-{org_a.pk}/logos/")
    assert key.endswith(".png")
    assert "My Logo" not in key
    assert key != company_logo_upload_to(company, "My Logo.PNG")


def test_logo_key_requires_organization():
    with pytest.raises(ValueError):
        company_logo_upload_to(Company(name="X"), "logo.png")
