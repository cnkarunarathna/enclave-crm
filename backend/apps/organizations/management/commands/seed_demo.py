"""
python manage.py seed_demo [--reset] [--force]

Creates two demo organizations with users for every role, companies and contacts.
Data is written through crm.services, so the activity log is filled realistically.
Safe to run repeatedly: an organization that already has companies is left as it is.
"""

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.activity.models import ActivityLog
from apps.crm import services
from apps.crm.models import Company, Contact
from apps.organizations.models import Organization, User
from apps.organizations.roles import Role

# Public demo password (documented in the README); never used outside DEBUG unless --force.
PASSWORD = "Passw0rd!123"  # noqa: S105

# (name, industry, country, [(full_name, email, phone, job title), ...])
ACME_COMPANIES = [
    ("Sunrise Hotels", "Hospitality", "Sri Lanka", [
        ("Nimal Perera", "nimal.perera@sunrisehotels.lk", "0771234567", "General Manager"),
        ("Ayesha Fernando", "ayesha@sunrisehotels.lk", "0772345678", "Sales Manager"),
        ("Kasun Silva", "kasun@sunrisehotels.lk", "", "Front Office Lead"),
    ]),
    ("Ceylon Tea Trails", "Hospitality", "Sri Lanka", [
        ("Dilani Jayasuriya", "dilani@teatrails.lk", "0713456789", "Reservations Head"),
        ("Ruwan Bandara", "ruwan@teatrails.lk", "", "Operations Manager"),
    ]),
    ("Maldives Blue Resorts", "Hospitality", "Maldives", [
        ("Ahmed Shareef", "ahmed@mblueresorts.mv", "9607771234", "Director of Sales"),
        ("Mariyam Zahir", "mariyam@mblueresorts.mv", "9607772345", "Guest Relations"),
        ("Ibrahim Nasir", "ibrahim@mblueresorts.mv", "", "Revenue Manager"),
    ]),
    ("Island Air Taxi", "Aviation", "Maldives", [
        ("Hassan Latheef", "hassan@islandair.mv", "9607773456", "Charter Sales"),
        ("Aishath Rasheed", "aishath@islandair.mv", "", "Operations"),
    ]),
    ("Serendib Tours", "Travel", "Sri Lanka", [
        ("Chaminda Wijesinghe", "chaminda@serendibtours.lk", "0774567890", "Managing Director"),
        ("Nadeesha Gunawardena", "nadeesha@serendibtours.lk", "0775678901", "Tour Coordinator"),
        ("Pradeep Kumara", "pradeep@serendibtours.lk", "", "Driver Lead"),
    ]),
    ("Himalayan Treks", "Travel", "Nepal", [
        ("Pemba Sherpa", "pemba@himalayantreks.np", "9779801234567", "Lead Guide"),
        ("Anita Gurung", "anita@himalayantreks.np", "", "Bookings"),
    ]),
    ("Kerala Backwater Cruises", "Travel", "India", [
        ("Arjun Menon", "arjun@keralacruises.in", "919876543210", "Owner"),
        ("Lakshmi Nair", "lakshmi@keralacruises.in", "919876543211", "Sales Executive"),
    ]),
    ("Lion City Events", "Events", "Singapore", [
        ("Wei Ling Tan", "weiling@lioncityevents.sg", "6591234567", "Event Director"),
        ("Rajesh Kumar", "rajesh@lioncityevents.sg", "", "Account Manager"),
    ]),
    ("TravelPay Solutions", "Finance", "Singapore", [
        ("Jason Lim", "jason@travelpay.sg", "6592345678", "Partnerships Lead"),
        ("Priya Raman", "priya@travelpay.sg", "", "Customer Success"),
    ]),
    ("Colombo Cabs", "Transport", "Sri Lanka", [
        ("Saman Rathnayake", "saman@colombocabs.lk", "0776789012", "Fleet Manager"),
        ("Tharindu Dias", "tharindu@colombocabs.lk", "", "Dispatcher"),
    ]),
    ("London Luxury Travel", "Travel", "United Kingdom", [
        ("Emily Clarke", "emily@londonluxury.co.uk", "447700900123", "Travel Designer"),
        ("James Whitfield", "james@londonluxury.co.uk", "", "Head of Partnerships"),
    ]),
    ("Spice Route Restaurants", "Food & Beverage", "Sri Lanka", [
        ("Rohan de Mel", "rohan@spiceroute.lk", "0777890123", "Group Chef"),
        ("Shalini Abeysekera", "shalini@spiceroute.lk", "", "Events Manager"),
    ]),
    ("Pinnacle Insurance", "", "Sri Lanka", [
        ("Mahesh Senanayake", "mahesh@pinnacle.lk", "0778901234", "Travel Insurance Lead"),
        ("Iresha Karunaratne", "iresha@pinnacle.lk", "", "Claims Officer"),
    ]),
]  # fmt: skip

# Same company name and a contact with the same email as Acme: per-tenant uniqueness.
BLUESKY_COMPANIES = [
    ("Sunrise Hotels", "Hospitality", "Sri Lanka", [
        ("Nimal Perera", "nimal.perera@sunrisehotels.lk", "0771234567", "General Manager"),
        ("Sanjeewa Herath", "sanjeewa@sunrisehotels.lk", "", "Groups Manager"),
    ]),
    ("Galle Fort Villas", "Hospitality", "Sri Lanka", [
        ("Fathima Rizvi", "fathima@gallefortvillas.lk", "0719012345", "Owner"),
        ("Dinesh Peiris", "dinesh@gallefortvillas.lk", "", "Concierge"),
    ]),
    ("Yala Safari Jeeps", "Travel", "Sri Lanka", [
        ("Lasantha Wickramasinghe", "lasantha@yalasafari.lk", "0770123456", "Tracker"),
        ("Gayan Mendis", "gayan@yalasafari.lk", "", "Bookings"),
    ]),
    ("Dubai Desert Adventures", "Travel", "United Arab Emirates", [
        ("Omar Al Farsi", "omar@desertadventures.ae", "971501234567", "Sales Manager"),
        ("Sara Haddad", "sara@desertadventures.ae", "", "Operations"),
    ]),
]  # fmt: skip

ORGANIZATIONS = [
    ("Acme Travel", Organization.Plan.PRO, "acme.test", ACME_COMPANIES),
    ("Blue Sky Tours", Organization.Plan.BASIC, "bluesky.test", BLUESKY_COMPANIES),
]

USERS = [
    ("admin", Role.ADMIN, "Alex", "Admin"),
    ("manager", Role.MANAGER, "Morgan", "Manager"),
    ("staff", Role.STAFF, "Sam", "Staff"),
]


class Command(BaseCommand):
    help = "Create demo organizations, users, companies and contacts (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo orgs first.")
        parser.add_argument(
            "--force", action="store_true", help="Allow running when DEBUG is False."
        )

    def handle(self, *args, reset=False, force=False, **options):
        if not settings.DEBUG and not force:
            raise CommandError("Refusing to seed demo data with DEBUG=False (use --force).")

        if reset:
            self._reset()

        for org_name, plan, domain, companies in ORGANIZATIONS:
            with transaction.atomic():
                org, _ = Organization.objects.get_or_create(
                    name=org_name, defaults={"subscription_plan": plan}
                )
                users = {key: self._user(org, domain, key, *spec) for key, *spec in USERS}
                if Company.all_objects.filter(organization=org).exists():
                    self.stdout.write(f"{org_name}: already has data, skipped.")
                    continue
                self._create_data(users, companies)
                self.stdout.write(self.style.SUCCESS(f"{org_name}: created."))

        self._print_summary()

    # --- helpers ---------------------------------------------------------------

    def _user(self, org, domain, key, role, first_name, last_name):
        user, _ = User.objects.update_or_create(
            email=f"{key}@{domain}",
            defaults={
                "organization": org,
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
            },
        )
        user.set_password(PASSWORD)  # always reset, so the printed password works
        user.save(update_fields=["password"])
        return user

    def _create_data(self, users, companies):
        """Mix of actors and actions, so the activity log looks like real usage."""
        created = []
        for index, (name, industry, country, contacts) in enumerate(companies):
            actor = users["admin"] if index % 2 == 0 else users["manager"]
            company = services.create_company(
                user=actor, data={"name": name, "industry": industry, "country": country}
            )
            for contact_index, (full_name, email, phone, job) in enumerate(contacts):
                # Staff may create contacts, so they author some of them.
                author = users["staff"] if contact_index == len(contacts) - 1 else actor
                services.create_contact(
                    user=author,
                    data={
                        "company": company,
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "role": job,
                    },
                )
            created.append(company)

        # A few updates and a delete, so every action type shows up in the log.
        renamed = created[1]
        services.update_company(
            user=users["manager"], company=renamed, data={"name": f"{renamed.name} Ltd"}
        )
        contact = Contact.objects.filter(company=created[0]).order_by("id").first()
        services.update_contact(
            user=users["manager"], contact=contact, data={"role": f"Senior {contact.role}"}
        )
        extra = services.create_contact(
            user=users["staff"],
            data={
                "company": created[-1],
                "full_name": "Temporary Contact",
                "email": f"temp@{users['admin'].email.split('@')[1]}",
                "phone": "",
                "role": "Intern",
            },
        )
        services.delete_contact(user=users["admin"], contact=extra)

    def _reset(self):
        orgs = Organization.objects.filter(name__in=[name for name, *_ in ORGANIZATIONS])
        for company in Company.all_objects.filter(organization__in=orgs):
            if company.logo:  # logos uploaded through the UI during a demo
                default_storage.delete(company.logo.name)
        # Deleting children first: every foreign key to Organization is PROTECT.
        ActivityLog.all_objects.filter(organization__in=orgs).delete()
        Contact.all_objects.filter(organization__in=orgs).delete()
        Company.all_objects.filter(organization__in=orgs).delete()
        User.objects.filter(organization__in=orgs).delete()
        count = orgs.count()
        orgs.delete()
        self.stdout.write(self.style.WARNING(f"Reset: removed {count} demo organization(s)."))

    def _print_summary(self):
        self.stdout.write("\nDemo users (password for all: " + self.style.SUCCESS(PASSWORD) + ")")
        for org_name, _, domain, _ in ORGANIZATIONS:
            emails = ", ".join(f"{key}@{domain}" for key, *_ in USERS)
            self.stdout.write(f"  {org_name:<15} {emails}")

        acme_company = Company.objects.filter(
            organization__name="Acme Travel", name="Sunrise Hotels"
        ).first()
        if acme_company:
            self.stdout.write(
                "\nCross-tenant demo: log in as admin@bluesky.test and open\n"
                f"  http://localhost:5173/companies/{acme_company.pk}\n"
                f"  or GET /api/v1/companies/{acme_company.pk}/  ->  404 Not found\n"
                f"(Acme's 'Sunrise Hotels' is id {acme_company.pk}; Blue Sky has its own "
                "'Sunrise Hotels' with a different id.)"
            )
