"""
Authentication service - user management, tokens, API keys.
"""
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from indexer_api.core.config import settings
from indexer_api.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from indexer_api.db.models import APIKey, Organization, User, UserRole
from indexer_api.schemas.auth import (
    APIKeyCreate,
    APIKeyCreated,
    Token,
    UserCreate,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # User Operations
    # ========================================================================

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with an organization."""
        # Check if email already exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")

        # Create organization
        slug = self._generate_slug(user_data.organization_name)
        org = Organization(
            name=user_data.organization_name,
            slug=slug,
        )
        self.db.add(org)
        await self.db.flush()

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            organization_id=org.id,
            role=UserRole.ADMIN,  # First user is admin
        )
        self.db.add(user)
        await self.db.flush()

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        return user

    async def create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for a user."""
        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "email": user.email,
                "role": user.role,
                "org_id": user.organization_id,
            },
        )
        refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> Token | None:
        """Refresh access token using refresh token."""
        user_id = verify_token(refresh_token, token_type="refresh")
        if not user_id:
            return None

        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None

        return await self.create_tokens(user)

    # ========================================================================
    # API Key Operations
    # ========================================================================

    async def create_api_key(
        self,
        org_id: str,
        user_id: str,
        key_data: APIKeyCreate,
    ) -> APIKeyCreated:
        """Create a new API key."""
        # Generate the key
        raw_key = f"idx_{secrets.token_urlsafe(32)}"
        key_hash = sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12] + "..."

        # Calculate expiry
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_in_days)

        api_key = APIKey(
            name=key_data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            organization_id=org_id,
            created_by_id=user_id,
            scopes=key_data.scopes,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()

        return APIKeyCreated(
            id=api_key.id,
            name=api_key.name,
            key_prefix=key_prefix,
            key=raw_key,  # Only returned on creation
            scopes=api_key.scopes,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
        )

    async def validate_api_key(self, raw_key: str) -> tuple[APIKey, Organization] | None:
        """Validate an API key and return the key + organization."""
        key_hash = sha256(raw_key.encode()).hexdigest()

        result = await self.db.execute(
            select(APIKey)
            .options(selectinload(APIKey.organization))
            .where(APIKey.key_hash == key_hash)
            .where(APIKey.is_active == True)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.flush()

        return api_key, api_key.organization

    async def list_api_keys(self, org_id: str) -> list[APIKey]:
        """List all API keys for an organization."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.organization_id == org_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_api_key(self, org_id: str, key_id: str) -> bool:
        """Revoke an API key."""
        result = await self.db.execute(
            select(APIKey)
            .where(APIKey.id == key_id)
            .where(APIKey.organization_id == org_id)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        api_key.is_active = False
        await self.db.flush()
        return True

    # ========================================================================
    # Helpers
    # ========================================================================

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-safe slug from a name."""
        import re
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        # Add random suffix for uniqueness
        slug = f"{slug}-{secrets.token_hex(4)}"
        return slug
