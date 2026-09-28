"""
The "current organization" for the running request.

A ContextVar is like a thread-local that also works with async code: each
request sees only its own value. TenantContextMiddleware sets it; TenantManager
reads it. Outside a request (shell, migrations, commands) it is None.
"""

from contextvars import ContextVar, Token

_current_org_id: ContextVar[int | None] = ContextVar("current_org_id", default=None)


def get_current_org_id() -> int | None:
    return _current_org_id.get()


def set_current_org_id(org_id: int | None) -> Token:
    # Returns a token so the caller can restore the previous value afterwards.
    return _current_org_id.set(org_id)


def reset_current_org_id(token: Token) -> None:
    _current_org_id.reset(token)
