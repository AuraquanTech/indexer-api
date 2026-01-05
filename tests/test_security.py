"""
Tests for security features:
- Fraud detection service
- PII masking in logs
- OWASP security headers
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from indexer_api.payments.fraud_detection import (
    FraudDetectionService,
    RedisFraudDetectionService,
    get_fraud_service,
    get_redis_fraud_service,
    FraudSignal,
    FraudCheckResult,
    REDIS_AVAILABLE,
)
from indexer_api.core.logging import mask_pii, PII_PATTERNS


# ============== Fraud Detection Tests ==============

class TestFraudDetection:
    """Tests for the fraud detection service."""

    def setup_method(self):
        """Create a fresh fraud service for each test."""
        self.fraud_svc = FraudDetectionService()

    def test_normal_transaction_approved(self):
        """Normal transactions should be approved."""
        result = self.fraud_svc.check_transaction(
            customer_email="user@gmail.com",
            amount_cents=2999,  # $29.99
            ip_address="192.168.1.1"
        )
        assert result.recommendation == "approve"
        assert result.total_risk_score < 0.3
        assert not result.is_suspicious

    def test_micro_transaction_flagged(self):
        """Micro transactions (<$1) should be flagged for review."""
        result = self.fraud_svc.check_transaction(
            customer_email="user@example.com",
            amount_cents=50,  # $0.50
            ip_address="10.0.0.1"
        )
        assert result.is_suspicious
        assert result.total_risk_score >= 0.6
        assert any(s.signal_type == "micro_transaction" for s in result.signals)

    def test_large_transaction_flagged(self):
        """Very large transactions (>$10k) should add risk."""
        result = self.fraud_svc.check_transaction(
            customer_email="user@example.com",
            amount_cents=1500000,  # $15,000
            ip_address="10.0.0.1"
        )
        assert any(s.signal_type == "large_transaction" for s in result.signals)
        assert result.total_risk_score > 0

    def test_disposable_email_flagged(self):
        """Disposable email domains should be flagged."""
        result = self.fraud_svc.check_transaction(
            customer_email="test@tempmail.com",
            amount_cents=5000,
            ip_address="10.0.0.1"
        )
        assert any(s.signal_type == "disposable_email" for s in result.signals)

    def test_velocity_check_per_minute(self):
        """Too many transactions per minute should be flagged."""
        # Make 4 transactions quickly (limit is 3/minute)
        for i in range(4):
            result = self.fraud_svc.check_transaction(
                customer_email="rapid@example.com",
                amount_cents=1000,
                ip_address="10.0.0.1"
            )

        # 4th transaction should trigger velocity check
        assert any(s.signal_type == "velocity_minute" for s in result.signals)

    def test_round_amount_flagged(self):
        """Large round amounts should add slight risk."""
        result = self.fraud_svc.check_transaction(
            customer_email="user@example.com",
            amount_cents=50000,  # $500 (round)
            ip_address="10.0.0.1"
        )
        assert any(s.signal_type == "round_amount" for s in result.signals)

    def test_numeric_email_flagged(self):
        """Emails with many numbers (auto-generated) should be flagged."""
        result = self.fraud_svc.check_transaction(
            customer_email="user123456789@example.com",
            amount_cents=5000,
            ip_address="10.0.0.1"
        )
        assert any(s.signal_type == "suspicious_email_pattern" for s in result.signals)

    def test_block_threshold(self):
        """High-risk transactions should be blocked."""
        # Create a service instance and simulate multiple risk factors
        svc = FraudDetectionService()

        # Micro transaction + disposable email + velocity should block
        for _ in range(4):  # Trigger velocity
            result = svc.check_transaction(
                customer_email="test@tempmail.com",  # Disposable
                amount_cents=50,  # Micro
                ip_address="10.0.0.1"
            )

        # Should be blocked with combined risk
        assert result.total_risk_score >= 0.6

    def test_reset_customer_signals(self):
        """Resetting customer signals should clear history."""
        # Build up velocity
        for _ in range(3):
            self.fraud_svc.check_transaction(
                customer_email="reset@example.com",
                amount_cents=1000,
                ip_address="10.0.0.1"
            )

        # Reset
        self.fraud_svc.reset_customer_signals("reset@example.com")

        # Should be clean now
        result = self.fraud_svc.check_transaction(
            customer_email="reset@example.com",
            amount_cents=1000,
            ip_address="10.0.0.1"
        )
        assert not any(s.signal_type.startswith("velocity") for s in result.signals)


# ============== PII Masking Tests ==============

class TestPIIMasking:
    """Tests for PII masking in logs."""

    def test_email_masking(self):
        """Email addresses should be partially masked."""
        test_input = "User email: test@example.com contacted us"
        result = mask_pii(test_input)

        assert "test@example.com" not in result
        assert "***" in result
        # Should preserve some context
        assert "tes" in result  # First 3 chars preserved

    def test_credit_card_masking(self):
        """Credit card numbers should show only last 4 digits."""
        test_input = "Card: 4111111111111111"
        result = mask_pii(test_input)

        assert "4111111111111111" not in result
        assert "1111" in result  # Last 4 preserved
        assert "****" in result

    def test_ssn_masking(self):
        """SSN should show only last 4 digits."""
        test_input = "SSN: 123-45-6789"
        result = mask_pii(test_input)

        assert "123-45-6789" not in result
        assert "6789" in result  # Last 4 preserved
        assert "***-**-" in result

    def test_stripe_key_masking(self):
        """Stripe API keys should be redacted."""
        test_input = "Key: sk_test_abc123def456ghi789jkl012mno345"
        result = mask_pii(test_input)

        # Should be partially masked
        assert "sk_test_abc123def456ghi789jkl012mno345" not in result or "REDACTED" in result

    def test_jwt_masking(self):
        """JWT tokens should be redacted."""
        test_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        test_input = f"Token: {test_jwt}"
        result = mask_pii(test_input)

        assert test_jwt not in result
        assert "REDACTED" in result

    def test_password_masking(self):
        """Password values in logs should be redacted."""
        test_input = 'password = "super_secret_123"'
        result = mask_pii(test_input)

        assert "super_secret_123" not in result
        assert "REDACTED" in result

    def test_dict_masking(self):
        """PII masking should work recursively on dicts."""
        test_input = {
            "user": "test@example.com",
            "card": "4111111111111111",
            "nested": {
                "ssn": "123-45-6789"
            }
        }
        result = mask_pii(test_input)

        assert "test@example.com" not in result["user"]
        assert "4111111111111111" not in result["card"]
        assert "123-45-6789" not in result["nested"]["ssn"]

    def test_list_masking(self):
        """PII masking should work on lists."""
        test_input = ["test@example.com", "other@example.com"]
        result = mask_pii(test_input)

        assert "test@example.com" not in result[0]
        assert "other@example.com" not in result[1]

    def test_non_pii_unchanged(self):
        """Non-PII strings should remain unchanged."""
        test_input = "Hello, this is a normal message without PII"
        result = mask_pii(test_input)

        assert result == test_input


# ============== Security Headers Tests ==============

@pytest.mark.asyncio
class TestSecurityHeaders:
    """Tests for OWASP security headers middleware."""

    async def test_x_content_type_options(self, client: AsyncClient):
        """X-Content-Type-Options header should be set."""
        response = await client.get("/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    async def test_x_frame_options(self, client: AsyncClient):
        """X-Frame-Options header should be set to DENY."""
        response = await client.get("/health")
        assert response.headers.get("x-frame-options") == "DENY"

    async def test_x_xss_protection(self, client: AsyncClient):
        """X-XSS-Protection header should be set."""
        response = await client.get("/health")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    async def test_strict_transport_security(self, client: AsyncClient):
        """Strict-Transport-Security header should be set."""
        response = await client.get("/health")
        hsts = response.headers.get("strict-transport-security")
        assert hsts is not None
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    async def test_referrer_policy(self, client: AsyncClient):
        """Referrer-Policy header should be set."""
        response = await client.get("/health")
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    async def test_permissions_policy(self, client: AsyncClient):
        """Permissions-Policy header should restrict features."""
        response = await client.get("/health")
        policy = response.headers.get("permissions-policy")
        assert policy is not None
        assert "geolocation=()" in policy
        assert "microphone=()" in policy
        assert "camera=()" in policy

    async def test_content_security_policy(self, client: AsyncClient):
        """Content-Security-Policy header should be set."""
        response = await client.get("/health")
        csp = response.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp


# ============== Integration Tests ==============

@pytest.mark.asyncio
class TestHealthEndpoints:
    """Tests for health check endpoints."""

    async def test_basic_health(self, client: AsyncClient):
        """Basic health endpoint should work."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "database" in data

    async def test_detailed_health(self, client: AsyncClient):
        """Detailed health endpoint should show all components."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()

        assert "components" in data
        assert "database" in data["components"]
        assert "redis" in data["components"]
        assert "stripe" in data["components"]

        assert "security" in data
        assert data["security"]["owasp_headers"] is True
        assert data["security"]["fraud_detection"] is True
        assert data["security"]["pii_masking"] is True


@pytest.mark.asyncio
class TestMonitoringEndpoints:
    """Tests for monitoring and alerting endpoints."""

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Metrics endpoint should return system metrics."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "timestamp" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "total_requests" in data
        assert "total_errors" in data
        assert "error_rate" in data
        assert "fraud_checks" in data

        # Fraud checks structure
        assert "total" in data["fraud_checks"]
        assert "flagged" in data["fraud_checks"]
        assert "blocked" in data["fraud_checks"]

    async def test_alerts_endpoint(self, client: AsyncClient):
        """Alerts endpoint should return alert status."""
        response = await client.get("/alerts")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "timestamp" in data
        assert "status" in data
        assert data["status"] in ["ok", "warning", "critical"]
        assert "alert_count" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    async def test_root_includes_new_endpoints(self, client: AsyncClient):
        """Root endpoint should list all available endpoints."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "metrics" in data
        assert "alerts" in data
        assert data["metrics"] == "/metrics"
        assert data["alerts"] == "/alerts"


# ============== Redis Fraud Detection Tests ==============

@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestRedisFraudDetection:
    """Tests for Redis-backed fraud detection service.

    These tests require Redis to be running locally.
    Skipped if Redis is not available or not running.
    """

    @pytest_asyncio.fixture
    async def redis_fraud_svc(self):
        """Create Redis fraud service for tests."""
        import redis.asyncio as aioredis
        # Try to connect to Redis
        try:
            redis = await aioredis.from_url("redis://localhost:6379/15")  # Use DB 15 for tests
            await redis.ping()
            await redis.flushdb()  # Clear test DB
            await redis.close()
        except Exception:
            pytest.skip("Redis not running or not accessible")

        svc = RedisFraudDetectionService(redis_url="redis://localhost:6379/15")
        yield svc
        await svc.close()

    async def test_redis_normal_transaction(self, redis_fraud_svc):
        """Normal transactions via Redis should be approved."""
        result = await redis_fraud_svc.check_transaction(
            customer_email="user@gmail.com",
            amount_cents=2999,
            ip_address="192.168.1.1"
        )
        assert result.recommendation == "approve"
        assert result.total_risk_score < 0.3

    async def test_redis_velocity_tracking(self, redis_fraud_svc):
        """Redis should track velocity across multiple transactions."""
        # Make 4 transactions to trigger velocity check
        for i in range(4):
            result = await redis_fraud_svc.check_transaction(
                customer_email="velocity@example.com",
                amount_cents=1000,
                ip_address="10.0.0.1"
            )

        # 4th should trigger velocity signal
        assert any(s.signal_type == "velocity_minute" for s in result.signals)

    async def test_redis_micro_transaction(self, redis_fraud_svc):
        """Micro transactions should be flagged in Redis."""
        result = await redis_fraud_svc.check_transaction(
            customer_email="test@example.com",
            amount_cents=50,  # $0.50
            ip_address="10.0.0.1"
        )
        assert result.is_suspicious
        assert any(s.signal_type == "micro_transaction" for s in result.signals)

    async def test_redis_disposable_email(self, redis_fraud_svc):
        """Disposable emails should be flagged in Redis."""
        result = await redis_fraud_svc.check_transaction(
            customer_email="test@tempmail.com",
            amount_cents=5000,
            ip_address="10.0.0.1"
        )
        assert any(s.signal_type == "disposable_email" for s in result.signals)

    async def test_redis_reset_signals(self, redis_fraud_svc):
        """Resetting signals in Redis should clear tracking."""
        # Build up velocity
        for _ in range(3):
            await redis_fraud_svc.check_transaction(
                customer_email="reset@example.com",
                amount_cents=1000,
                ip_address="10.0.0.1"
            )

        # Reset
        await redis_fraud_svc.reset_customer_signals("reset@example.com")

        # Should be clean now
        result = await redis_fraud_svc.check_transaction(
            customer_email="reset@example.com",
            amount_cents=1000,
            ip_address="10.0.0.1"
        )
        assert not any(s.signal_type.startswith("velocity") for s in result.signals)
