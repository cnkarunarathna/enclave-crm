from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Organization, User, normalize_email
from .roles import capabilities_for

INVALID_CREDENTIALS = "Invalid email or password."
INVALID_REFRESH = "Invalid or expired refresh token."


class OrganizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "subscription_plan"]


class UserSerializer(serializers.ModelSerializer):
    """The signed-in user, as returned by /auth/login and /auth/me."""

    full_name = serializers.CharField(read_only=True)
    organization = OrganizationSummarySerializer(read_only=True)
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "organization", "capabilities"]

    def get_capabilities(self, user) -> dict:
        return capabilities_for(user.role)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = normalize_email(attrs["email"])
        password = attrs["password"]
        user = User.objects.select_related("organization").filter(email=email).first()

        if user is None:
            # Hash anyway so "unknown email" takes as long as "wrong password"
            # (prevents discovering which emails exist by timing).
            User().set_password(password)
            raise exceptions.AuthenticationFailed(INVALID_CREDENTIALS)
        if not user.check_password(password):
            raise exceptions.AuthenticationFailed(INVALID_CREDENTIALS)
        # Correct password but not allowed to use the API (e.g. admin-only superuser).
        if not user.is_active or user.organization_id is None:
            raise exceptions.PermissionDenied("This account is not allowed to sign in.")

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)  # also rejects already-blacklisted tokens
        except TokenError as exc:
            raise serializers.ValidationError(INVALID_REFRESH) from exc
        # A user may only revoke their own session.
        if str(token.get("user_id")) != str(self.context["request"].user.pk):
            raise serializers.ValidationError(INVALID_REFRESH)
        return token
