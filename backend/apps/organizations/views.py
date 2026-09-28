from django.contrib.auth.models import update_last_login
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import LoginSerializer, LogoutSerializer, UserSerializer
from .tokens import issue_tokens


class LoginView(APIView):
    """POST {email, password} -> {access, refresh, user}. Rate limited per IP."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def get_authenticate_header(self, request):
        # Without this, DRF turns 401 into 403 on views with no authentication classes.
        return 'Bearer realm="api"'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        update_last_login(None, user)
        return Response({**issue_tokens(user), "user": UserSerializer(user).data})


class LogoutView(APIView):
    """POST {refresh} -> blacklists the refresh token so it can't mint new access tokens."""

    def post(self, request):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["refresh"].blacklist()
        return Response({"success": True, "message": "Logged out.", "data": None})


class MeView(APIView):
    """GET the current user, organization and role capabilities."""

    def get(self, request):
        return Response(UserSerializer(request.user).data)
