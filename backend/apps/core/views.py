from django.db import DatabaseError, connection
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import error_body


class HealthView(APIView):
    """Liveness + database check for load balancers and Docker healthchecks."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError:
            return Response(error_body("Database unavailable.", "service_unavailable"), status=503)
        return Response({"status": "ok"})


# Django-level handlers (used when DEBUG=False) so non-DRF errors are JSON too.
def not_found(request, exception=None):
    return JsonResponse(error_body("Not found.", "not_found"), status=404)


def server_error(request):
    return JsonResponse(error_body("An unexpected error occurred.", "server_error"), status=500)
