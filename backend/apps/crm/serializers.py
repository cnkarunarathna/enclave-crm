"""
Validation and representation only. Writes happen in crm.services.

`organization`, `is_deleted`, `deleted_at` and timestamps are never accepted
from the client: they are simply not writable fields here.
"""

from rest_framework import serializers

from apps.core.validators import normalize_phone, validate_logo

from .models import Company, Contact

DUPLICATE_EMAIL = "A contact with this email already exists for this company."


class CompanySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(
        write_only=True, required=False, allow_null=True, validators=[validate_logo]
    )
    remove_logo = serializers.BooleanField(write_only=True, required=False, default=False)
    logo_url = serializers.SerializerMethodField()
    contacts_count = serializers.IntegerField(read_only=True)  # annotated in the viewset

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "industry",
            "country",
            "logo",
            "remove_logo",
            "logo_url",
            "contacts_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_logo_url(self, company) -> str | None:
        if not company.logo:
            return None
        # S3: a presigned URL that expires. Local storage: /media/..., made absolute.
        url = company.logo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request and url.startswith("/") else url

    def validate(self, attrs):
        if attrs.get("logo") and attrs.get("remove_logo"):
            raise serializers.ValidationError(
                {"remove_logo": ["Send a new logo or remove_logo, not both."]}
            )
        return attrs


class TenantCompanyField(serializers.PrimaryKeyRelatedField):
    """
    Accepts only companies of the requesting user's organization (and not deleted).
    Without this, a user could attach a contact to another tenant's company id.
    """

    default_error_messages = {
        "does_not_exist": "Company not found.",
        "incorrect_type": "Company must be an id.",
    }

    def get_queryset(self):
        user = self.context["request"].user
        return Company.objects.for_org(user.organization_id)


class ContactSerializer(serializers.ModelSerializer):
    company = TenantCompanyField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    # No max_length here: the limit applies to digits *after* removing spaces,
    # which validate_phone checks (the model column is 15 chars).
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "company",
            "company_name",
            "full_name",
            "email",
            "phone",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        # We check email uniqueness ourselves (clear message, soft-delete aware);
        # the partial unique index in the DB is the race-condition backstop.
        validators = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["company"].required = False  # immutable after creation

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate(self, attrs):
        company = attrs.get("company")
        if self.instance is not None:
            if company is not None and company != self.instance.company:
                raise serializers.ValidationError({"company": ["Company cannot be changed."]})
            company = self.instance.company

        email = attrs.get("email")
        if email is not None:
            duplicates = Contact.objects.filter(company=company, email=email)
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError({"email": [DUPLICATE_EMAIL]})
        return attrs
