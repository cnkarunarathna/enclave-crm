from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .tenancy import reset_current_org_id, set_current_org_id


class TenantContextMiddleware:
    """
    Sets the current organization (ContextVar) for the duration of a request.

    DRF authenticates inside the view, so `request.user` is not known here yet.
    Instead we read the org_id claim from the signed JWT ourselves. This middleware
    never rejects a request: DRF's JWTAuthentication still decides 401s.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = set_current_org_id(self._org_id_from(request))
        try:
            return self.get_response(request)
        finally:
            # Always restore, so one request's org can never leak into the next.
            reset_current_org_id(token)

    @staticmethod
    def _org_id_from(request) -> int | None:
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Bearer "):
            return None
        try:
            # Verifies signature, expiry and token type (refresh tokens are rejected).
            return AccessToken(header.removeprefix("Bearer ")).get("org_id")
        except TokenError:
            return None
