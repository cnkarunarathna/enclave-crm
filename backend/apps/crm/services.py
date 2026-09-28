"""
Every write to Company and Contact goes through here.

Each function runs in one database transaction: the change and its activity-log
row are saved together, or not at all. `organization` always comes from the
acting user (or the parent company), never from client input.
"""

from django.db import transaction
from django.utils import timezone

from apps.activity.models import ActivityLog
from apps.activity.services import (
    bulk_log_activity,
    diff_values,
    field_values,
    log_activity,
    snapshot,
)

from .models import Company, Contact

Action = ActivityLog.Action

# Fields recorded in the audit log.
COMPANY_FIELDS = ["name", "industry", "country", "logo"]
CONTACT_FIELDS = ["company", "full_name", "email", "phone", "role"]


# --- Companies ---------------------------------------------------------------


@transaction.atomic
def create_company(*, user, data) -> Company:
    data = {k: v for k, v in data.items() if k != "remove_logo"}
    # organization is set before save() so the logo's storage key can use it.
    company = Company(organization_id=user.organization_id, **data)
    company.save()
    log_activity(
        user=user, action=Action.CREATE, obj=company, changes=snapshot(company, COMPANY_FIELDS)
    )
    return company


@transaction.atomic
def update_company(*, user, company, data) -> Company:
    data = dict(data)
    remove_logo = data.pop("remove_logo", False)
    before = field_values(company, COMPANY_FIELDS)
    old_logo = company.logo.name or None

    for field, value in data.items():
        setattr(company, field, value)
    if remove_logo:
        company.logo = None
    company.save()

    changes = diff_values(before, field_values(company, COMPANY_FIELDS))
    log_activity(user=user, action=Action.UPDATE, obj=company, changes=changes)

    new_logo = company.logo.name or None
    if old_logo and old_logo != new_logo:
        # Delete the replaced file only once the transaction has committed.
        storage = Company._meta.get_field("logo").storage
        transaction.on_commit(lambda: storage.delete(old_logo))
    return company


@transaction.atomic
def delete_company(*, user, company) -> None:
    """Soft delete the company and cascade to its active contacts (each one logged)."""
    now = timezone.now()
    contacts = list(Contact.objects.for_org(user.organization_id).filter(company=company))

    company.is_deleted = True
    company.deleted_at = now
    company.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
    # QuerySet.update() skips auto_now, so updated_at is set explicitly.
    Contact.all_objects.filter(pk__in=[c.pk for c in contacts]).update(
        is_deleted=True, deleted_at=now, updated_at=now
    )

    log_activity(user=user, action=Action.DELETE, obj=company)
    bulk_log_activity(user=user, action=Action.DELETE, objs=contacts)
    # Logo files are kept on soft delete (the record still exists).


# --- Contacts ----------------------------------------------------------------


@transaction.atomic
def create_contact(*, user, data) -> Contact:
    company = data["company"]  # already tenant-scoped and active (serializer)
    contact = Contact(organization_id=company.organization_id, **data)
    contact.save()
    log_activity(
        user=user, action=Action.CREATE, obj=contact, changes=snapshot(contact, CONTACT_FIELDS)
    )
    return contact


@transaction.atomic
def update_contact(*, user, contact, data) -> Contact:
    data = {k: v for k, v in data.items() if k != "company"}  # company never changes
    before = field_values(contact, CONTACT_FIELDS)

    for field, value in data.items():
        setattr(contact, field, value)
    contact.save()

    changes = diff_values(before, field_values(contact, CONTACT_FIELDS))
    log_activity(user=user, action=Action.UPDATE, obj=contact, changes=changes)
    return contact


@transaction.atomic
def delete_contact(*, user, contact) -> None:
    contact.is_deleted = True
    contact.deleted_at = timezone.now()
    contact.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
    log_activity(user=user, action=Action.DELETE, obj=contact)
