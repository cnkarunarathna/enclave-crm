from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q

from .roles import Role


class Organization(models.Model):
    """A tenant. Every piece of business data belongs to exactly one organization."""

    class Plan(models.TextChoices):
        BASIC = "BASIC", "Basic"
        PRO = "PRO", "Pro"

    name = models.CharField(max_length=150, unique=True)
    subscription_plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.BASIC)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Email is the login identifier; there is no username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        user = self.model(email=normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        # Superusers are for Django admin only and may have no organization.
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self._create_user(email, password, **extra_fields)


def normalize_email(email: str) -> str:
    return email.strip().lower()


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    # Nullable only so a Django-admin superuser can exist; see the check constraint.
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]
        constraints = [
            models.CheckConstraint(
                condition=Q(organization__isnull=False) | Q(is_superuser=True),
                name="user_org_required_unless_superuser",
            ),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return self.get_full_name() or self.email
