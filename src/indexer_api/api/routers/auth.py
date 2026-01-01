"""
Authentication router - login, register, tokens, API keys.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from indexer_api.api.deps import CurrentUser, DbSession
from indexer_api.schemas.auth import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyResponse,
    OrganizationResponse,
    RefreshTokenRequest,
    Token,
    UserCreate,
    UserResponse,
    UserWithOrganization,
)
from indexer_api.schemas.base import SuccessResponse
from indexer_api.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Registration & Login
# ============================================================================


@router.post(
    "/register",
    response_model=UserWithOrganization,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and organization",
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserWithOrganization:
    """
    Register a new user account with an organization.

    - Creates a new organization
    - Creates the first user as admin
    - Returns user details with organization
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.create_user(user_data)
        await db.commit()

        # Reload user with organization to avoid lazy loading in async context
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from indexer_api.db.models import User

        result = await db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user.id)
        )
        user = result.scalar_one()

        return UserWithOrganization(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            organization_id=user.organization_id,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            organization=OrganizationResponse(
                id=user.organization.id,
                name=user.organization.name,
                slug=user.organization.slug,
                subscription_tier=user.organization.subscription_tier,
                max_indexes=user.organization.max_indexes,
                max_files_per_index=user.organization.max_files_per_index,
                max_storage_mb=user.organization.max_storage_mb,
                current_storage_mb=user.organization.current_storage_mb,
                api_calls_this_month=user.organization.api_calls_this_month,
                created_at=user.organization.created_at,
                updated_at=user.organization.updated_at,
            ),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> Token:
    """
    OAuth2 compatible token login.

    Returns access and refresh tokens.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await auth_service.create_tokens(user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DbSession,
) -> Token:
    """
    Get new access token using refresh token.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(request.refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return tokens


# ============================================================================
# Current User
# ============================================================================


@router.get(
    "/me",
    response_model=UserWithOrganization,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserWithOrganization:
    """Get the current authenticated user's profile."""
    return UserWithOrganization(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        organization_id=current_user.organization_id,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        organization=OrganizationResponse(
            id=current_user.organization.id,
            name=current_user.organization.name,
            slug=current_user.organization.slug,
            subscription_tier=current_user.organization.subscription_tier,
            max_indexes=current_user.organization.max_indexes,
            max_files_per_index=current_user.organization.max_files_per_index,
            max_storage_mb=current_user.organization.max_storage_mb,
            current_storage_mb=current_user.organization.current_storage_mb,
            api_calls_this_month=current_user.organization.api_calls_this_month,
            created_at=current_user.organization.created_at,
            updated_at=current_user.organization.updated_at,
        ),
    )


# ============================================================================
# API Keys
# ============================================================================


@router.post(
    "/api-keys",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> APIKeyCreated:
    """
    Create a new API key for programmatic access.

    The full key is only shown once on creation!
    """
    auth_service = AuthService(db)

    api_key = await auth_service.create_api_key(
        org_id=current_user.organization_id,
        user_id=current_user.id,
        key_data=key_data,
    )

    return api_key


@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    summary="List API keys",
)
async def list_api_keys(
    current_user: CurrentUser,
    db: DbSession,
) -> list[APIKeyResponse]:
    """List all API keys for the current organization."""
    auth_service = AuthService(db)
    keys = await auth_service.list_api_keys(current_user.organization_id)

    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            scopes=key.scopes,
            is_active=key.is_active,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            created_at=key.created_at,
        )
        for key in keys
    ]


@router.delete(
    "/api-keys/{key_id}",
    response_model=SuccessResponse,
    summary="Revoke an API key",
)
async def revoke_api_key(
    key_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> SuccessResponse:
    """Revoke (disable) an API key."""
    auth_service = AuthService(db)
    success = await auth_service.revoke_api_key(
        org_id=current_user.organization_id,
        key_id=key_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return SuccessResponse(message="API key revoked")
