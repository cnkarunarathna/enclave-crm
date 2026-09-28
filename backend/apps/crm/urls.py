from rest_framework.routers import SimpleRouter

from .views import CompanyViewSet, ContactViewSet

router = SimpleRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("contacts", ContactViewSet, basename="contact")

urlpatterns = router.urls
