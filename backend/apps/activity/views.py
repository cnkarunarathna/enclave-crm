from apps.core.viewsets import OrganizationScopedReadOnlyViewSet

from .filters import ActivityLogFilter
from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(OrganizationScopedReadOnlyViewSet):
    """Read-only audit log for the user's organization (Admin and Manager)."""

    model = ActivityLog
    permission_resource = "activity_log"
    serializer_class = ActivityLogSerializer
    filterset_class = ActivityLogFilter
    search_fields = ["object_repr", "user_email"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp", "-id"]

    def get_queryset(self):
        return super().get_queryset().select_related("user")  # avoid N+1 on user
