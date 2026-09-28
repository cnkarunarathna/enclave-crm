"""Input validation: contact email/phone and company logo uploads."""

import os
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from .factories import make_company, make_contact, make_image

CONTACTS = "/api/v1/contacts/"
COMPANIES = "/api/v1/companies/"

pytestmark = pytest.mark.django_db


@pytest.fixture
def company(org_a):
    return make_company(org_a)


@pytest.fixture
def post_contact(auth_client, admin_a, company):
    client = auth_client(admin_a)

    def _post(**fields):
        payload = {"company": company.pk, "full_name": "Jane Doe", "email": "jane@example.com"}
        return client.post(CONTACTS, {**payload, **fields}, format="json")

    return _post


# --- Email -------------------------------------------------------------------


def test_invalid_email_is_rejected(post_contact):
    res = post_contact(email="not-an-email")

    assert res.status_code == 400
    assert "email" in res.json()["errors"]


def test_duplicate_email_in_same_company_is_rejected(post_contact, company):
    make_contact(company, email="jane@example.com")

    res = post_contact(email="JANE@example.com")

    assert res.status_code == 400
    assert res.json()["errors"]["email"] == [
        "A contact with this email already exists for this company."
    ]


def test_same_email_in_another_company_is_allowed(post_contact, org_a):
    make_contact(make_company(org_a, name="Other"), email="jane@example.com")

    assert post_contact(email="jane@example.com").status_code == 201


def test_updating_a_contact_keeps_its_own_email(auth_client, admin_a, company):
    contact = make_contact(company, email="jane@example.com")

    res = auth_client(admin_a).patch(
        f"{CONTACTS}{contact.pk}/", {"email": "jane@example.com", "role": "CTO"}, format="json"
    )

    assert res.status_code == 200


def test_updating_to_a_taken_email_is_rejected(auth_client, admin_a, company):
    make_contact(company, email="taken@example.com")
    contact = make_contact(company, email="jane@example.com")

    res = auth_client(admin_a).patch(
        f"{CONTACTS}{contact.pk}/", {"email": "taken@example.com"}, format="json"
    )

    assert res.status_code == 400
    assert "email" in res.json()["errors"]


# --- Phone -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("phone", "stored"),
    [
        ("12345678", "12345678"),
        ("123456789012345", "123456789012345"),
        ("077 123 4567", "0771234567"),
        ("1234 5678 9012 345", "123456789012345"),  # 15 digits, spaces allowed
        ("", ""),
    ],
)
def test_valid_phones(post_contact, phone, stored):
    res = post_contact(phone=phone)

    assert res.status_code == 201
    assert res.json()["data"]["phone"] == stored


def test_phone_is_optional(post_contact):
    assert post_contact().status_code == 201


@pytest.mark.parametrize("phone", ["1234567", "1234567890123456", "07712345ab", "+94771234567"])
def test_invalid_phones(post_contact, phone):
    res = post_contact(phone=phone)

    assert res.status_code == 400
    assert res.json()["errors"]["phone"] == ["Phone must be 8–15 digits."]


# --- Logo --------------------------------------------------------------------


@pytest.fixture
def post_company(auth_client, admin_a):
    client = auth_client(admin_a)

    def _post(logo):
        return client.post(COMPANIES, {"name": "Logo Co", "logo": logo}, format="multipart")

    return _post


@pytest.mark.parametrize(
    ("name", "image_format", "content_type"),
    [
        ("a.png", "PNG", "image/png"),
        ("a.jpg", "JPEG", "image/jpeg"),
        ("a.webp", "WEBP", "image/webp"),
    ],
)
def test_allowed_logo_types(post_company, name, image_format, content_type):
    assert post_company(make_image(name, image_format, content_type)).status_code == 201


def test_gif_logo_is_rejected(post_company):
    res = post_company(make_image("a.gif", "GIF", "image/gif"))

    assert res.status_code == 400
    assert "logo" in res.json()["errors"]


def test_svg_logo_is_rejected(post_company):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    res = post_company(SimpleUploadedFile("a.svg", svg, content_type="image/svg+xml"))

    assert res.status_code == 400
    assert "logo" in res.json()["errors"]


def test_non_image_with_png_name_is_rejected(post_company):
    fake = SimpleUploadedFile("a.png", b"definitely not a png", content_type="image/png")

    assert post_company(fake).status_code == 400


def test_png_bytes_with_wrong_extension_are_rejected(post_company):
    assert post_company(make_image("a.exe", "PNG", "image/png")).status_code == 400


def test_oversized_logo_is_rejected(post_company, settings):
    settings.MAX_LOGO_SIZE_MB = 0.001  # ~1 KB
    # Random pixels don't compress, so this PNG is ~30 KB.
    buffer = BytesIO()
    Image.frombytes("RGB", (100, 100), os.urandom(100 * 100 * 3)).save(buffer, format="PNG")

    res = post_company(SimpleUploadedFile("big.png", buffer.getvalue(), content_type="image/png"))

    assert res.status_code == 400
    assert res.json()["errors"]["logo"] == ["Logo must be 0.001 MB or smaller."]
