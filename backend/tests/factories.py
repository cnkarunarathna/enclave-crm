"""Tiny helpers to create test data. Plain functions keep tests easy to read."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.crm.models import Company, Contact
from apps.organizations.models import User

PASSWORD = "Passw0rd!123"


def make_user(email, organization, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, organization=organization, role=role
    )


def make_company(organization, name="Sunrise Hotels", **fields):
    return Company.objects.create(organization=organization, name=name, **fields)


def make_contact(company, email="jane@example.com", full_name="Jane Doe", **fields):
    return Contact.objects.create(
        organization_id=company.organization_id,
        company=company,
        email=email,
        full_name=full_name,
        **fields,
    )


def make_image(name="logo.png", image_format="PNG", content_type="image/png", size=(8, 8)):
    """A real (tiny) image upload, generated in memory."""
    buffer = BytesIO()
    Image.new("RGB", size, "orange").save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)
