from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("timestamp", "organization", "user_email", "action", "model_name", "object_id")
    list_filter = ("organization", "action", "model_name")
    search_fields = ("object_repr", "user_email")
    list_select_related = ("organization",)
