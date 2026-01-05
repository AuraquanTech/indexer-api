"""
Legal Documents Module for IndexerAPI
Provides Privacy Policy, Terms of Service, Refund Policy, and Cookie Policy
"""

from .privacy_policy import get_privacy_policy, PRIVACY_POLICY
from .terms_of_service import get_terms_of_service, TERMS_OF_SERVICE
from .refund_policy import get_refund_policy, REFUND_POLICY
from .cookie_policy import get_cookie_policy, COOKIE_POLICY

__all__ = [
    "get_privacy_policy",
    "get_terms_of_service",
    "get_refund_policy",
    "get_cookie_policy",
    "PRIVACY_POLICY",
    "TERMS_OF_SERVICE",
    "REFUND_POLICY",
    "COOKIE_POLICY",
]
