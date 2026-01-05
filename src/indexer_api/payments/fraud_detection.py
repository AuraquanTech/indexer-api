"""
Payment Fraud Detection Service

Based on knowledge base patterns from:
- Payment Intelligence System cursor-ingest.json
- Secret patterns for detecting suspicious data

Features:
- Real-time payment pattern analysis
- Anomaly detection based on velocity checks
- Risk scoring for transactions
"""
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from indexer_api.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FraudSignal:
    """A fraud detection signal with risk score."""
    signal_type: str
    description: str
    risk_score: float  # 0.0 to 1.0
    metadata: Optional[Dict] = None


@dataclass
class FraudCheckResult:
    """Result of a fraud check."""
    is_suspicious: bool
    total_risk_score: float
    signals: List[FraudSignal]
    recommendation: str  # "approve", "review", "block"


class FraudDetectionService:
    """
    Service for detecting fraudulent payment patterns.

    Based on Payment Intelligence System knowledge pack:
    - Velocity checks (too many transactions in short time)
    - Amount anomalies (unusual transaction amounts)
    - Geographic anomalies (if IP data available)
    - Behavioral patterns
    """

    # Risk thresholds
    THRESHOLD_APPROVE = 0.3
    THRESHOLD_REVIEW = 0.6
    THRESHOLD_BLOCK = 0.85

    # Velocity limits
    MAX_TRANSACTIONS_PER_MINUTE = 3
    MAX_TRANSACTIONS_PER_HOUR = 10
    MAX_AMOUNT_PER_HOUR = 100000  # cents ($1000)

    def __init__(self):
        # In-memory storage for velocity tracking (use Redis in production)
        self._transaction_times: Dict[str, List[float]] = defaultdict(list)
        self._transaction_amounts: Dict[str, List[int]] = defaultdict(list)
        self._email_transaction_counts: Dict[str, int] = defaultdict(int)

    def check_transaction(
        self,
        customer_email: Optional[str],
        amount_cents: int,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> FraudCheckResult:
        """
        Check a transaction for fraud signals.

        Args:
            customer_email: Customer's email address
            amount_cents: Transaction amount in cents
            ip_address: Customer's IP address (optional)
            metadata: Additional transaction metadata

        Returns:
            FraudCheckResult with signals and recommendation
        """
        signals: List[FraudSignal] = []
        identifier = customer_email or ip_address or "unknown"

        # Check 1: Velocity - transactions per minute
        velocity_signal = self._check_velocity(identifier)
        if velocity_signal:
            signals.append(velocity_signal)

        # Check 2: Amount anomaly
        amount_signal = self._check_amount_anomaly(identifier, amount_cents)
        if amount_signal:
            signals.append(amount_signal)

        # Check 3: Hourly spending limit
        spending_signal = self._check_hourly_spending(identifier, amount_cents)
        if spending_signal:
            signals.append(spending_signal)

        # Check 4: Email pattern (disposable email domains)
        if customer_email:
            email_signal = self._check_email_pattern(customer_email)
            if email_signal:
                signals.append(email_signal)

        # Check 5: Round amount check (often indicates testing)
        if amount_cents > 0 and amount_cents % 10000 == 0:  # Round $100s
            if amount_cents >= 50000:  # $500+
                signals.append(FraudSignal(
                    signal_type="round_amount",
                    description="Large round amount transaction",
                    risk_score=0.2
                ))

        # Calculate total risk score
        total_risk = sum(s.risk_score for s in signals)
        total_risk = min(total_risk, 1.0)  # Cap at 1.0

        # Determine recommendation
        if total_risk >= self.THRESHOLD_BLOCK:
            recommendation = "block"
        elif total_risk >= self.THRESHOLD_REVIEW:
            recommendation = "review"
        else:
            recommendation = "approve"

        # Record transaction for future velocity checks
        self._record_transaction(identifier, amount_cents)

        result = FraudCheckResult(
            is_suspicious=total_risk >= self.THRESHOLD_REVIEW,
            total_risk_score=total_risk,
            signals=signals,
            recommendation=recommendation
        )

        # Log suspicious transactions
        if result.is_suspicious:
            logger.warning(
                "suspicious_transaction_detected",
                risk_score=result.total_risk_score,
                recommendation=result.recommendation,
                signal_count=len(signals),
                # Don't log customer_email - PII masking will handle it if needed
            )

        return result

    def _check_velocity(self, identifier: str) -> Optional[FraudSignal]:
        """Check transaction velocity (too many in short time)."""
        now = time.time()
        recent_times = self._transaction_times.get(identifier, [])

        # Clean old entries (keep last hour)
        recent_times = [t for t in recent_times if now - t < 3600]
        self._transaction_times[identifier] = recent_times

        # Check per-minute velocity
        last_minute = [t for t in recent_times if now - t < 60]
        if len(last_minute) >= self.MAX_TRANSACTIONS_PER_MINUTE:
            return FraudSignal(
                signal_type="velocity_minute",
                description=f"Too many transactions in last minute ({len(last_minute)})",
                risk_score=0.5,
                metadata={"count": len(last_minute), "window": "minute"}
            )

        # Check per-hour velocity
        if len(recent_times) >= self.MAX_TRANSACTIONS_PER_HOUR:
            return FraudSignal(
                signal_type="velocity_hour",
                description=f"Too many transactions in last hour ({len(recent_times)})",
                risk_score=0.3,
                metadata={"count": len(recent_times), "window": "hour"}
            )

        return None

    def _check_amount_anomaly(
        self,
        identifier: str,
        amount_cents: int
    ) -> Optional[FraudSignal]:
        """Check for unusual transaction amounts."""
        # Very small amounts (card testing)
        if 0 < amount_cents < 100:  # Less than $1
            return FraudSignal(
                signal_type="micro_transaction",
                description="Unusually small transaction (possible card testing)",
                risk_score=0.6,
                metadata={"amount_cents": amount_cents}
            )

        # Very large amounts
        if amount_cents > 1000000:  # More than $10,000
            return FraudSignal(
                signal_type="large_transaction",
                description="Unusually large transaction",
                risk_score=0.3,
                metadata={"amount_cents": amount_cents}
            )

        return None

    def _check_hourly_spending(
        self,
        identifier: str,
        amount_cents: int
    ) -> Optional[FraudSignal]:
        """Check if hourly spending limit is exceeded."""
        now = time.time()
        recent_amounts = self._transaction_amounts.get(identifier, [])

        # This is simplified - in production use timestamps with amounts
        total_recent = sum(recent_amounts[-self.MAX_TRANSACTIONS_PER_HOUR:])

        if total_recent + amount_cents > self.MAX_AMOUNT_PER_HOUR:
            return FraudSignal(
                signal_type="spending_limit",
                description="Hourly spending limit exceeded",
                risk_score=0.4,
                metadata={
                    "recent_total": total_recent,
                    "new_amount": amount_cents,
                    "limit": self.MAX_AMOUNT_PER_HOUR
                }
            )

        return None

    def _check_email_pattern(self, email: str) -> Optional[FraudSignal]:
        """Check for suspicious email patterns."""
        # Disposable email domains (sample list)
        disposable_domains = {
            "tempmail.com", "throwaway.com", "guerrillamail.com",
            "10minutemail.com", "mailinator.com", "temp-mail.org",
            "fakeinbox.com", "trashmail.com"
        }

        domain = email.split("@")[-1].lower() if "@" in email else ""

        if domain in disposable_domains:
            return FraudSignal(
                signal_type="disposable_email",
                description="Disposable email domain detected",
                risk_score=0.5,
                metadata={"domain": domain}
            )

        # Check for random-looking email (lots of numbers)
        local_part = email.split("@")[0] if "@" in email else email
        digit_ratio = sum(c.isdigit() for c in local_part) / len(local_part) if local_part else 0

        if digit_ratio > 0.5:  # More than 50% numbers
            return FraudSignal(
                signal_type="suspicious_email_pattern",
                description="Email appears auto-generated",
                risk_score=0.2,
                metadata={"digit_ratio": digit_ratio}
            )

        return None

    def _record_transaction(self, identifier: str, amount_cents: int) -> None:
        """Record a transaction for velocity tracking."""
        now = time.time()
        self._transaction_times[identifier].append(now)
        self._transaction_amounts[identifier].append(amount_cents)

        # Cleanup old entries (keep last 24 hours)
        cutoff = now - 86400
        self._transaction_times[identifier] = [
            t for t in self._transaction_times[identifier] if t > cutoff
        ]
        self._transaction_amounts[identifier] = self._transaction_amounts[identifier][-100:]

    def reset_customer_signals(self, identifier: str) -> None:
        """Reset fraud signals for a customer (e.g., after verification)."""
        self._transaction_times.pop(identifier, None)
        self._transaction_amounts.pop(identifier, None)
        self._email_transaction_counts.pop(identifier, None)


# Singleton instance
_fraud_service: Optional[FraudDetectionService] = None


def get_fraud_service() -> FraudDetectionService:
    """Get or create fraud detection service singleton."""
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudDetectionService()
    return _fraud_service
