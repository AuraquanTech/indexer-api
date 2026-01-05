"""
License Key Generation Service
Generates, validates, and manages software license keys
"""
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for license key generation and validation"""

    # License key format: XXXX-XXXX-XXXX-XXXX (16 chars + 3 dashes)
    KEY_LENGTH = 16
    SEGMENT_LENGTH = 4

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize with optional secret for key generation"""
        self.secret_key = secret_key or secrets.token_hex(32)

    def generate_license_key(
        self,
        product_id: UUID,
        customer_id: UUID,
        order_id: UUID
    ) -> str:
        """
        Generate a unique license key for a purchase
        Format: XXXX-XXXX-XXXX-XXXX
        """
        # Create a unique seed from order details
        seed = f"{product_id}:{customer_id}:{order_id}:{datetime.utcnow().isoformat()}:{secrets.token_hex(8)}"

        # Hash the seed with our secret
        hash_input = f"{seed}:{self.secret_key}".encode()
        hash_bytes = hashlib.sha256(hash_input).digest()

        # Encode and format
        encoded = base64.b32encode(hash_bytes).decode()[:self.KEY_LENGTH].upper()

        # Format as XXXX-XXXX-XXXX-XXXX
        segments = [encoded[i:i+self.SEGMENT_LENGTH] for i in range(0, self.KEY_LENGTH, self.SEGMENT_LENGTH)]
        license_key = "-".join(segments)

        return license_key

    def generate_activation_code(self, license_key: str, machine_id: str) -> str:
        """Generate an activation code tied to a specific machine"""
        seed = f"{license_key}:{machine_id}:{self.secret_key}"
        hash_bytes = hashlib.sha256(seed.encode()).digest()
        return base64.b32encode(hash_bytes).decode()[:8].upper()

    def validate_license_format(self, license_key: str) -> bool:
        """Check if license key has valid format"""
        if not license_key:
            return False

        # Remove dashes and check length
        clean_key = license_key.replace("-", "")
        if len(clean_key) != self.KEY_LENGTH:
            return False

        # Check format (alphanumeric only)
        if not clean_key.isalnum():
            return False

        # Check segment count
        segments = license_key.split("-")
        if len(segments) != 4:
            return False

        return True

    def generate_download_token(
        self,
        product_id: UUID,
        order_id: UUID,
        expires_hours: int = 24
    ) -> Tuple[str, datetime]:
        """
        Generate a time-limited download token
        Returns (token, expiry_datetime)
        """
        expiry = datetime.utcnow() + timedelta(hours=expires_hours)

        seed = f"{product_id}:{order_id}:{expiry.isoformat()}:{self.secret_key}"
        hash_bytes = hashlib.sha256(seed.encode()).digest()
        token = base64.urlsafe_b64encode(hash_bytes).decode()[:32]

        return token, expiry

    def verify_download_token(
        self,
        token: str,
        product_id: UUID,
        order_id: UUID,
        expiry: datetime
    ) -> bool:
        """Verify a download token is valid and not expired"""
        if datetime.utcnow() > expiry:
            return False

        # Regenerate expected token
        seed = f"{product_id}:{order_id}:{expiry.isoformat()}:{self.secret_key}"
        hash_bytes = hashlib.sha256(seed.encode()).digest()
        expected_token = base64.urlsafe_b64encode(hash_bytes).decode()[:32]

        return secrets.compare_digest(token, expected_token)


# Singleton instance
_license_service: Optional[LicenseService] = None


def get_license_service() -> LicenseService:
    """Get or create license service singleton"""
    global _license_service
    if _license_service is None:
        _license_service = LicenseService()
    return _license_service
