"""(Optional service) API key authentication.

Authentication is disabled by default (AUTH_ENABLED=false). When enabled,
every request must carry an Authorization: Bearer <api-key> header whose
value matches the API_KEY environment variable.

Usage in a route:
    @router.post("/convert", dependencies=[Depends(require_auth)])
    def convert(...): ...

Or inject the result to get the key back:
    @router.post("/convert")
    def convert(key: AuthDep): ...
"""

from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import SettingsDep
from app.exceptions import AuthenticationError

_bearer_scheme = HTTPBearer(auto_error=False)


async def require_auth(
    settings: SettingsDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(_bearer_scheme)
    ],
) -> str | None:
    """FastAPI dependency that enforces API key authentication.

    When AUTH_ENABLED is false this is a no-op and returns None.
    When AUTH_ENABLED is true:
    - Raises AuthenticationError (401) if no Bearer token is provided.
    - Raises AuthenticationError (401) if the token does not match API_KEY.
    - Returns the verified token string on success.
    """
    if not settings.auth_enabled:
        return None

    if credentials is None:
        raise AuthenticationError("Authentication required. Provide a Bearer token.")

    if not settings.api_key:
        raise AuthenticationError("Server misconfiguration: API_KEY is not set.")

    if credentials.credentials != settings.api_key:
        raise AuthenticationError("Invalid API key.")

    return credentials.credentials


# Convenience type alias for route signatures:
#   async def my_route(auth: AuthDep) -> ...:
AuthDep = Annotated[str | None, Depends(require_auth)]
