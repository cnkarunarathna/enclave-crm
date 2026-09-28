"""Root URL configuration. All API routes live under the versioned /api/v1/ prefix."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # TODO(phase 1+): path("api/v1/", include(...)) for auth, crm, activity, dashboard, health
]

if settings.DEBUG and getattr(settings, "MEDIA_URL", None):
    # Local FileSystemStorage only; S3 serves its own (presigned) URLs.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
