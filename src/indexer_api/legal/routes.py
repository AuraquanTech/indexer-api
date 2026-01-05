"""
Legal Routes for IndexerAPI
Serves Privacy Policy, Terms of Service, Refund Policy, and Cookie Policy
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .privacy_policy import get_privacy_policy
from .terms_of_service import get_terms_of_service
from .refund_policy import get_refund_policy
from .cookie_policy import get_cookie_policy
from .data_processing_agreement import get_data_processing_agreement

router = APIRouter(prefix="/legal", tags=["Legal"])


@router.get("/privacy", response_class=HTMLResponse, summary="Privacy Policy")
async def privacy_policy():
    """
    Returns the Privacy Policy for IndexerAPI.

    This document explains how we collect, use, and protect your personal information
    in compliance with GDPR, CCPA, and other applicable privacy regulations.
    """
    return get_privacy_policy()


@router.get("/terms", response_class=HTMLResponse, summary="Terms of Service")
async def terms_of_service():
    """
    Returns the Terms of Service for IndexerAPI.

    This document outlines the rules and guidelines for using our service,
    including acceptable use, payment terms, and limitations of liability.
    """
    return get_terms_of_service()


@router.get("/refund", response_class=HTMLResponse, summary="Refund Policy")
async def refund_policy():
    """
    Returns the Refund and Cancellation Policy for IndexerAPI.

    This document explains our refund eligibility, cancellation process,
    and money-back guarantee terms.
    """
    return get_refund_policy()


@router.get("/cookies", response_class=HTMLResponse, summary="Cookie Policy")
async def cookie_policy():
    """
    Returns the Cookie Policy for IndexerAPI.

    This document explains what cookies we use, why we use them,
    and how you can manage your cookie preferences.
    """
    return get_cookie_policy()


@router.get("/dpa", response_class=HTMLResponse, summary="Data Processing Agreement")
async def data_processing_agreement():
    """
    Returns the Data Processing Agreement (DPA) for IndexerAPI.

    This document is a GDPR Article 28 compliant agreement for enterprise
    customers who require a formal data processing agreement.
    """
    return get_data_processing_agreement()


# JSON versions for API consumers
@router.get("/privacy.json", summary="Privacy Policy (JSON)")
async def privacy_policy_json():
    """Returns Privacy Policy metadata in JSON format."""
    return {
        "title": "Privacy Policy",
        "effective_date": "2026-01-05",
        "last_updated": "2026-01-05",
        "url": "/legal/privacy",
        "contact": "privacy@ayrto.dev",
        "dpo_contact": "dpo@ayrto.dev"
    }


@router.get("/terms.json", summary="Terms of Service (JSON)")
async def terms_of_service_json():
    """Returns Terms of Service metadata in JSON format."""
    return {
        "title": "Terms of Service",
        "effective_date": "2026-01-05",
        "last_updated": "2026-01-05",
        "url": "/legal/terms",
        "contact": "legal@ayrto.dev",
        "governing_law": "Delaware, United States"
    }


@router.get("/refund.json", summary="Refund Policy (JSON)")
async def refund_policy_json():
    """Returns Refund Policy metadata in JSON format."""
    return {
        "title": "Refund and Cancellation Policy",
        "effective_date": "2026-01-05",
        "last_updated": "2026-01-05",
        "url": "/legal/refund",
        "contact": "billing@ayrto.dev",
        "money_back_guarantee_days": 14,
        "refund_processing_days": "5-10 business days"
    }


@router.get("/cookies.json", summary="Cookie Policy (JSON)")
async def cookie_policy_json():
    """Returns Cookie Policy metadata in JSON format."""
    return {
        "title": "Cookie Policy",
        "effective_date": "2026-01-05",
        "last_updated": "2026-01-05",
        "url": "/legal/cookies",
        "contact": "privacy@ayrto.dev",
        "cookie_categories": ["essential", "functional", "analytics"],
        "marketing_cookies": False
    }


@router.get("/dpa.json", summary="Data Processing Agreement (JSON)")
async def dpa_json():
    """Returns Data Processing Agreement metadata in JSON format."""
    return {
        "title": "Data Processing Agreement",
        "effective_date": "2026-01-05",
        "last_updated": "2026-01-05",
        "version": "1.0",
        "url": "/legal/dpa",
        "contact": "dpo@ayrto.dev",
        "gdpr_compliant": True,
        "sccs_included": True,
        "breach_notification_hours": 48,
        "sub_processors": ["Railway", "Stripe", "Resend"]
    }


@router.get("/", summary="Legal Documents Index")
async def legal_index():
    """Returns a list of all available legal documents."""
    return {
        "documents": [
            {
                "name": "Privacy Policy",
                "description": "How we collect, use, and protect your data",
                "html_url": "/legal/privacy",
                "json_url": "/legal/privacy.json"
            },
            {
                "name": "Terms of Service",
                "description": "Rules and guidelines for using IndexerAPI",
                "html_url": "/legal/terms",
                "json_url": "/legal/terms.json"
            },
            {
                "name": "Refund Policy",
                "description": "Refund eligibility and cancellation process",
                "html_url": "/legal/refund",
                "json_url": "/legal/refund.json"
            },
            {
                "name": "Cookie Policy",
                "description": "Information about cookies and tracking",
                "html_url": "/legal/cookies",
                "json_url": "/legal/cookies.json"
            },
            {
                "name": "Data Processing Agreement",
                "description": "GDPR Article 28 compliant DPA for enterprise customers",
                "html_url": "/legal/dpa",
                "json_url": "/legal/dpa.json"
            }
        ],
        "company": "Ayrto Engineering",
        "contact": {
            "general": "support@ayrto.dev",
            "legal": "legal@ayrto.dev",
            "privacy": "privacy@ayrto.dev",
            "billing": "billing@ayrto.dev"
        }
    }
