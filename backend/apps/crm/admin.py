from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import Company, Contact


@admin.register(Company)
class CompanyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "organization", "industry", "country", "is_deleted", "created_at")
    list_filter = ("organization", "is_deleted")
    search_fields = ("name",)
    list_select_related = ("organization",)

    def get_queryset(self, request):
        # Platform view: include soft-deleted rows.
        return Company.all_objects.select_related("organization")


@admin.register(Contact)
class ContactAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("full_name", "email", "company", "organization", "is_deleted", "created_at")
    list_filter = ("organization", "is_deleted")
    search_fields = ("full_name", "email")

    def get_queryset(self, request):
        return Contact.all_objects.select_related("organization", "company")
