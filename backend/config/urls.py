"""Root URL configuration. All API routes live under the versioned /api/v1/ prefix."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import HealthView

api_v1 = [
    path("auth/", include("apps.organizations.urls")),
    path("", include("apps.crm.urls")),
    path("", include("apps.activity.urls")),
    path("", include("apps.dashboard.urls")),
    path("health/", HealthView.as_view(), name="health"),
]

if settings.API_DOCS_ENABLED:
    # Schema shows raw serializers; the real responses are wrapped in the envelope.
    api_v1 += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

if settings.DEBUG and getattr(settings, "MEDIA_URL", None):
    # Local FileSystemStorage only; S3 serves its own (presigned) URLs.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# JSON instead of HTML error pages (active when DEBUG=False).
handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"
