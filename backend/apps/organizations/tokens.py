from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user) -> dict[str, str]:
    """
    Create a refresh/access pair with our custom claims.

    Claims set on the refresh token are copied into every access token minted
    from it (including after rotation), so org_id is always present.
    TenantContextMiddleware reads `org_id`; permissions still use the DB user.
    """
    refresh = RefreshToken.for_user(user)
    refresh["org_id"] = user.organization_id
    refresh["role"] = user.role
    refresh["email"] = user.email
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
