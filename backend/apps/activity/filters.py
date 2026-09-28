import django_filters

from .models import ActivityLog


class ActivityLogFilter(django_filters.FilterSet):
    # Plain number filters (not model choice) so a foreign user id is not
    # "validated" against the whole users table, which would reveal it exists.
    user = django_filters.NumberFilter(field_name="user_id")
    object_id = django_filters.NumberFilter()
    # Dates (YYYY-MM-DD), inclusive on both ends.
    timestamp_after = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__gte")
    timestamp_before = django_filters.DateFilter(field_name="timestamp", lookup_expr="date__lte")

    class Meta:
        model = ActivityLog
        fields = ["model_name", "action", "user", "object_id"]
