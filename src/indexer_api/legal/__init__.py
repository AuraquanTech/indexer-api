"""
Legal Documents Module for IndexerAPI
Provides Privacy Policy, Terms of Service, Refund Policy, Cookie Policy, and DPA
"""

from .privacy_policy import get_privacy_policy, PRIVACY_POLICY
from .terms_of_service import get_terms_of_service, TERMS_OF_SERVICE
from .refund_policy import get_refund_policy, REFUND_POLICY
from .cookie_policy import get_cookie_policy, COOKIE_POLICY
from .data_processing_agreement import get_data_processing_agreement, DATA_PROCESSING_AGREEMENT

__all__ = [
    "get_privacy_policy",
    "get_terms_of_service",
    "get_refund_policy",
    "get_cookie_policy",
    "get_data_processing_agreement",
    "PRIVACY_POLICY",
    "TERMS_OF_SERVICE",
    "REFUND_POLICY",
    "COOKIE_POLICY",
    "DATA_PROCESSING_AGREEMENT",
]
