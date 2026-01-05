"""
Secrets Scanner - A comprehensive tool for detecting exposed secrets.

Features:
- Pattern-based detection for 80+ secret types (API keys, tokens, credentials)
- Entropy-based detection for unknown/custom secrets
- Multi-source scanning: files, environment, cloud configs, git history, registry
- Integration with ai-credentials store
- Parallel scanning for speed
- Detailed reporting with confidence scores

Usage:
    from secrets_scanner import SecretsScanner

    scanner = SecretsScanner()
    result = scanner.full_scan(
        directories=[Path("/path/to/project")],
        scan_env=True,
        scan_cloud=True,
    )

    for secret in result.secrets:
        print(f"{secret.secret_type}: {secret.masked_value}")

CLI:
    python -m secrets_scanner scan /path/to/scan
    python -m secrets_scanner scan --env --cloud --registry
    python -m secrets_scanner report
"""

from .scanner import (
    SecretsScanner,
    SecretMatch,
    ScanResult,
    ScanSource,
    mask_secret,
)
from .patterns import (
    SecretType,
    SecretPattern,
    SECRET_PATTERNS,
    get_env_var_name,
)
from .entropy import (
    analyze_entropy,
    calculate_shannon_entropy,
    extract_high_entropy_strings,
    EntropyResult,
)
from .integrations import (
    add_to_credentials_store,
    batch_add_to_credentials,
    get_existing_keys,
    generate_report,
    export_to_env_template,
    CredentialStoreConfig,
)

__version__ = "1.0.0"
__author__ = "AI Assistant"
__all__ = [
    # Scanner
    "SecretsScanner",
    "SecretMatch",
    "ScanResult",
    "ScanSource",
    "mask_secret",
    # Patterns
    "SecretType",
    "SecretPattern",
    "SECRET_PATTERNS",
    "get_env_var_name",
    # Entropy
    "analyze_entropy",
    "calculate_shannon_entropy",
    "extract_high_entropy_strings",
    "EntropyResult",
    # Integrations
    "add_to_credentials_store",
    "batch_add_to_credentials",
    "get_existing_keys",
    "generate_report",
    "export_to_env_template",
    "CredentialStoreConfig",
]
