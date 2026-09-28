"""Input validators shared by serializers. The API is the authority; the UI only mirrors these."""

import re
from pathlib import Path

from django.conf import settings
from rest_framework import serializers

PHONE_PATTERN = re.compile(r"^\d{8,15}$")

# SVG is deliberately excluded: it can carry scripts.
ALLOWED_LOGO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_LOGO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def normalize_phone(value: str) -> str:
    """Optional phone: spaces are removed, then 8-15 digits are required."""
    digits = (value or "").replace(" ", "")
    if digits and not PHONE_PATTERN.match(digits):
        raise serializers.ValidationError("Phone must be 8–15 digits.")
    return digits


def validate_logo(file) -> None:
    """
    Runs after DRF's ImageField has opened the file with Pillow, so a non-image
    is already rejected and `content_type` reflects the real bytes, not the
    browser's claim.
    """
    if Path(file.name).suffix.lower() not in ALLOWED_LOGO_EXTENSIONS:
        raise serializers.ValidationError("Logo must be a .jpg, .jpeg, .png or .webp file.")
    if getattr(file, "content_type", None) not in ALLOWED_LOGO_CONTENT_TYPES:
        raise serializers.ValidationError("Logo must be a JPEG, PNG or WebP image.")
    max_bytes = settings.MAX_LOGO_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise serializers.ValidationError(
            f"Logo must be {settings.MAX_LOGO_SIZE_MB} MB or smaller."
        )
