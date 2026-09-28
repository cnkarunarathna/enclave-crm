from rest_framework.routers import SimpleRouter

from .views import ActivityLogViewSet

router = SimpleRouter()
router.register("activity-logs", ActivityLogViewSet, basename="activity-log")

urlpatterns = router.urls
