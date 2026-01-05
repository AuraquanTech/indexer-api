# Knowledge Base Implementations for IndexerAPI

## Summary

Solutions extracted and applied from:
- `C:\Users\ayrto\CentralKnowledgeBase` (security, devtools, UI patterns)
- `C:\Users\ayrto\OneDrive\Master Knoledge Agentic Base` (payment intelligence, fraud detection)

---

## Security Enhancements Applied

### 1. Webhook Signature Validation (HMAC-SHA256)
**Source:** Payment Intelligence System, OWASP A02:2021

**File:** `src/indexer_api/payments/stripe_service.py`

- Implemented HMAC-SHA256 signature validation using Stripe's built-in verification
- Added timestamp extraction and freshness validation
- 5-minute tolerance window for replay attack prevention
- Structured security logging without exposing sensitive data

```python
def verify_webhook_signature(self, payload, sig_header, tolerance=300):
    # Returns (event, is_replay_safe) tuple
```

### 2. Timestamp Replay Attack Prevention
**Source:** Payment Intelligence System (cc_01: Cryptographic Payment Verification)

- Webhooks older than 5 minutes are flagged
- Timestamp extracted from Stripe signature header
- Age validation before processing

### 3. OWASP Security Headers Middleware
**Source:** `CentralKnowledgeBase/security/owasp_top_10.json`

**File:** `src/indexer_api/main.py`

Headers added:
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Legacy XSS protection
- `Strict-Transport-Security` - HSTS enforcement
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` - Disables geolocation, microphone, camera
- `Content-Security-Policy` - Restricts resource loading

### 4. PII Masking in Logs
**Source:** `CentralKnowledgeBase/security/pii_patterns.json`, `secret_patterns.json`

**File:** `src/indexer_api/core/logging.py`

Patterns masked:
- Email addresses (partial masking)
- Credit card numbers (show only last 4)
- Social Security Numbers (show only last 4)
- API keys (Stripe, GitHub, OpenAI, Anthropic)
- JWT tokens
- Passwords in log strings

---

## Payment Security Enhancements

### 5. Fraud Detection Service
**Source:** Payment Intelligence System cursor-ingest.json (cc_04: Payment Event Embeddings)

**File:** `src/indexer_api/payments/fraud_detection.py`

Features:
- **Velocity Checks**: Max 3 transactions/minute, 10/hour
- **Amount Anomaly Detection**: Flags micro-transactions (<$1) and large amounts (>$10,000)
- **Spending Limits**: $1,000/hour limit per customer
- **Email Pattern Analysis**: Detects disposable email domains
- **Risk Scoring**: 0.0-1.0 scale with recommendations (approve/review/block)

Integration in checkout:
```python
fraud_result = fraud_svc.check_transaction(
    customer_email=customer_email,
    amount_cents=product.price_cents,
    ip_address=client_ip
)
if fraud_result.recommendation == "block":
    raise HTTPException(403, "Transaction cannot be processed")
```

---

## Infrastructure Enhancements

### 6. Enhanced Health Checks
**Source:** DevsTool Analyser Knowledge Pack

**File:** `src/indexer_api/api/routers/health.py`

Endpoints:
- `GET /health` - Basic health with DB/Redis status
- `GET /health/detailed` - Comprehensive check with:
  - Database connectivity + latency
  - Redis connectivity + latency
  - Stripe service status (configured/test/live)
  - Security feature status (headers, rate limiting, PII masking, fraud detection)
  - Total check time in milliseconds

---

## Security Patterns Reference

### From OWASP Top 10 (owasp_top_10.json)

| ID | Risk | Applied |
|----|------|---------|
| A01:2021 | Broken Access Control | ✅ Security headers |
| A02:2021 | Cryptographic Failures | ✅ HMAC-SHA256 webhooks |
| A03:2021 | Injection | ✅ Parameterized queries |
| A05:2021 | Security Misconfiguration | ✅ CORS/CSP headers |
| A07:2021 | Authentication Failures | ✅ JWT validation |

### From CWE Patterns (cwe_patterns.json)

| CWE | Name | Status |
|-----|------|--------|
| CWE-798 | Hardcoded Credentials | ✅ Env vars |
| CWE-352 | CSRF | ✅ State tokens |
| CWE-327 | Weak Crypto | ✅ SHA-256 |

---

## Files Modified

1. `src/indexer_api/payments/stripe_service.py` - Enhanced webhook verification
2. `src/indexer_api/payments/routes.py` - Fraud detection integration
3. `src/indexer_api/payments/fraud_detection.py` - NEW: Fraud detection service
4. `src/indexer_api/main.py` - Security headers middleware
5. `src/indexer_api/core/logging.py` - PII masking processor
6. `src/indexer_api/api/routers/health.py` - Enhanced health checks

---

## Future Recommendations

From Knowledge Base analysis:

1. **Add Rate Limiting per Endpoint** - Different limits for checkout vs. read operations
2. **Implement Redis-backed Fraud Detection** - Replace in-memory tracking
3. **Add Webhook Idempotency** - Prevent duplicate order processing
4. **Geographic Risk Scoring** - IP-based location analysis
5. **Customer Risk Profiles** - Build historical risk data

---

*Generated from Central Knowledge Base and Master Knowledge Agentic Base*
*Last Updated: January 2026*
