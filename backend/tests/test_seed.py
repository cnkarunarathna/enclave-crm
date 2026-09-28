from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.activity.models import ActivityLog
from apps.crm.models import Company, Contact
from apps.organizations.models import Organization, User

from .factories import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _debug(settings):
    settings.DEBUG = True  # pytest-django runs with DEBUG=False; the seed refuses that


def seed(*args):
    call_command("seed_demo", *args, stdout=StringIO())


def counts():
    return (
        Organization.objects.count(),
        User.objects.count(),
        Company.all_objects.count(),
        Contact.all_objects.count(),
        ActivityLog.objects.count(),
    )


def test_seed_is_idempotent():
    seed()
    first = counts()
    seed()

    assert counts() == first
    assert first[:2] == (2, 6)


def test_seed_creates_the_documented_demo(api_client):
    seed()
    acme = Organization.objects.get(name="Acme Travel")
    bluesky = Organization.objects.get(name="Blue Sky Tours")

    assert Company.objects.for_org(acme).count() >= 11  # enough to paginate at 10
    assert Company.objects.for_org(bluesky).count() == 4
    # Same company name and contact email exist in both tenants.
    assert Company.objects.filter(name="Sunrise Hotels").count() == 2
    assert Contact.objects.filter(email="nimal.perera@sunrisehotels.lk").count() == 2
    # Every action type appears in the log.
    assert set(ActivityLog.objects.values_list("action", flat=True)) == {
        "CREATE",
        "UPDATE",
        "DELETE",
    }
    for email in ["admin@acme.test", "manager@acme.test", "staff@bluesky.test"]:
        res = api_client.post(
            "/api/v1/auth/login/", {"email": email, "password": PASSWORD}, format="json"
        )
        assert res.status_code == 200, email


def test_reset_recreates_the_demo():
    seed()
    Company.objects.filter(name="Sunrise Hotels").update(name="Changed")

    seed("--reset")

    assert Company.objects.filter(name="Changed").count() == 0
    assert Company.objects.filter(name="Sunrise Hotels").count() == 2


def test_refuses_to_run_without_debug(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError):
        seed()

    seed("--force")
    assert Organization.objects.count() == 2
