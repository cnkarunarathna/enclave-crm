from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm

from apps.core.admin import SuperuserOnlyMixin

from .models import Organization, User


@admin.register(Organization)
class OrganizationAdmin(SuperuserOnlyMixin, admin.ModelAdmin):
    list_display = ("name", "subscription_plan", "created_at")
    list_filter = ("subscription_plan",)
    search_fields = ("name",)


# Django's stock user forms assume a `username` field, so point them at our model.
class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "organization", "role")


class UserChangeForm(DjangoUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(SuperuserOnlyMixin, DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("email", "organization", "role", "is_active")
    list_filter = ("organization", "role", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name")}),
        ("Tenant", {"fields": ("organization", "role")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "organization", "role", "password1", "password2"),
            },
        ),
    )
