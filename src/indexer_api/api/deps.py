"""
API dependencies - authentication, rate limiting, etc.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from indexer_api.core.security import verify_token
from indexer_api.db.base import get_db
from indexer_api.db.models import APIKey, Organization, User
from indexer_api.services.auth import AuthService

# OAuth2 scheme for JWT tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    """Get current authenticated user from JWT token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_token(token, token_type="access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None

    try:
        return await get_current_user(db, token)
    except HTTPException:
        return None


async def get_api_key_auth(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[str | None, Security(api_key_header)],
) -> tuple[APIKey, Organization]:
    """Authenticate via API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    auth_service = AuthService(db)
    result = await auth_service.validate_api_key(api_key)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return result


async def get_auth_context(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme)],
    api_key: Annotated[str | None, Security(api_key_header)],
) -> tuple[str, str | None]:
    """
    Get authentication context from either JWT or API key.
    Returns (organization_id, user_id or None).
    """
    # Try JWT first
    if token:
        user_id = verify_token(token, token_type="access")
        if user_id:
            auth_service = AuthService(db)
            user = await auth_service.get_user_by_id(user_id)
            if user and user.is_active:
                return user.organization_id, user.id

    # Try API key
    if api_key:
        auth_service = AuthService(db)
        result = await auth_service.validate_api_key(api_key)
        if result:
            api_key_obj, org = result
            return org.id, None

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def require_role(*roles: str):
    """Dependency factory for role-based access control."""

    async def check_role(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}",
            )
        return user

    return check_role


def require_scope(*scopes: str):
    """Dependency factory for API key scope checking."""

    async def check_scope(
        auth: Annotated[tuple[APIKey, Organization], Depends(get_api_key_auth)],
    ) -> tuple[APIKey, Organization]:
        api_key, org = auth
        for scope in scopes:
            if scope not in api_key.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required scope: {scope}",
                )
        return api_key, org

    return check_scope


# Type aliases for cleaner route definitions
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
AuthContext = Annotated[tuple[str, str | None], Depends(get_auth_context)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
