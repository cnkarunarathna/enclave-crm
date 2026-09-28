from pathlib import Path
from uuid import uuid4


def company_logo_upload_to(instance, filename: str) -> str:
    """
    Storage key for a company logo: org-{org_id}/logos/{random}.{ext}

    - Prefixing by org keeps tenants' files apart and lets the IAM policy be scoped.
    - A random name avoids collisions and never leaks the user's original filename.
    """
    if instance.organization_id is None:
        # The organization must be set before the file is saved (see crm.services).
        raise ValueError("Company.organization must be set before saving a logo.")
    extension = Path(filename).suffix.lower()
    return f"org-{instance.organization_id}/logos/{uuid4().hex}{extension}"
