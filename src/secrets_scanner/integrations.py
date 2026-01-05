"""
Integration with the ai-credentials store.
Allows saving discovered secrets to the centralized credential store.
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .scanner import SecretMatch, ScanResult
from .patterns import SecretType, get_env_var_name


# Default location for ai-credentials store
DEFAULT_CREDENTIALS_DIR = Path.home() / ".ai-credentials"
DEFAULT_ENV_FILE = DEFAULT_CREDENTIALS_DIR / "api-keys.env"
DEFAULT_ADD_SCRIPT = DEFAULT_CREDENTIALS_DIR / "add-key.ps1"


@dataclass
class CredentialStoreConfig:
    """Configuration for the credential store."""
    credentials_dir: Path = DEFAULT_CREDENTIALS_DIR
    env_file: Path = DEFAULT_ENV_FILE
    add_script: Path = DEFAULT_ADD_SCRIPT


def get_existing_keys(config: CredentialStoreConfig = None) -> dict[str, str]:
    """Get all existing keys from the credential store (masked)."""
    if config is None:
        config = CredentialStoreConfig()

    keys = {}
    if not config.env_file.exists():
        return keys

    with open(config.env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                name, value = line.split('=', 1)
                name = name.strip()
                value = value.strip()
                if value:
                    # Mask the value
                    if len(value) > 8:
                        masked = f"{value[:4]}****{value[-4:]}"
                    else:
                        masked = "****"
                    keys[name] = masked

    return keys


def suggest_key_name(secret: SecretMatch) -> str:
    """Suggest an appropriate environment variable name for a secret."""
    # First check if the pattern has suggested names
    env_name = get_env_var_name(secret.secret_type)

    # Try to extract from location/context
    if secret.location and secret.location.startswith("$"):
        # Already an env var
        return secret.location[1:]

    # Use the default for this secret type
    return env_name


def format_for_env_file(name: str, value: str) -> str:
    """Format a key-value pair for the env file."""
    # Clean the name
    name = re.sub(r'[^A-Z0-9_]', '_', name.upper())
    return f"{name}={value}"


def add_to_credentials_store(
    secret: SecretMatch,
    key_name: Optional[str] = None,
    config: CredentialStoreConfig = None,
    overwrite: bool = False,
) -> tuple[bool, str]:
    """
    Add a discovered secret to the credential store.

    Returns:
        (success, message)
    """
    if config is None:
        config = CredentialStoreConfig()

    if key_name is None:
        key_name = suggest_key_name(secret)

    # Check if credentials directory exists
    if not config.credentials_dir.exists():
        return False, f"Credentials directory not found: {config.credentials_dir}"

    # Check if key already exists
    existing = get_existing_keys(config)
    if key_name in existing and not overwrite:
        return False, f"Key '{key_name}' already exists (use overwrite=True to replace)"

    # Read current env file
    if config.env_file.exists():
        with open(config.env_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# AI Assistant API Keys\n# Format: KEY_NAME=value\n\n"

    # Check if key exists in content
    key_pattern = re.compile(rf'^{re.escape(key_name)}\s*=.*$', re.MULTILINE)

    if key_pattern.search(content):
        if overwrite:
            content = key_pattern.sub(format_for_env_file(key_name, secret.value), content)
        else:
            return False, f"Key '{key_name}' already exists in file"
    else:
        # Add new key
        content = content.rstrip() + f"\n{format_for_env_file(key_name, secret.value)}\n"

    # Write back
    with open(config.env_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return True, f"Added {key_name} to {config.env_file}"


def batch_add_to_credentials(
    secrets: list[SecretMatch],
    config: CredentialStoreConfig = None,
    overwrite: bool = False,
    interactive: bool = False,
) -> list[tuple[SecretMatch, bool, str]]:
    """
    Add multiple secrets to the credential store.

    Returns:
        List of (secret, success, message) tuples
    """
    results = []

    for secret in secrets:
        key_name = suggest_key_name(secret)

        if interactive:
            # In interactive mode, ask for confirmation
            print(f"\nFound {secret.secret_type.value}:")
            print(f"  Value: {secret.masked_value}")
            print(f"  Location: {secret.location}")
            print(f"  Suggested name: {key_name}")
            response = input("Add to store? [y/N/custom name]: ").strip()

            if response.lower() == 'n' or not response:
                results.append((secret, False, "Skipped by user"))
                continue
            elif response.lower() != 'y':
                key_name = response

        success, message = add_to_credentials_store(
            secret, key_name, config, overwrite
        )
        results.append((secret, success, message))

    return results


def generate_report(
    result: ScanResult,
    existing_keys: dict[str, str] = None,
    output_format: str = "text",
) -> str:
    """Generate a report of scan results."""
    if existing_keys is None:
        existing_keys = get_existing_keys()

    if output_format == "json":
        import json
        report = {
            "scan_summary": {
                "files_scanned": result.files_scanned,
                "directories_scanned": result.directories_scanned,
                "secrets_found": len(result.secrets),
                "duration_seconds": result.scan_duration_seconds,
            },
            "secrets": [s.to_dict() for s in result.secrets],
            "existing_keys": list(existing_keys.keys()),
            "errors": result.errors,
        }
        return json.dumps(report, indent=2)

    # Text format
    lines = [
        "=" * 60,
        "SECRETS SCAN REPORT",
        "=" * 60,
        f"Scan completed: {result.scan_started.isoformat()}",
        f"Duration: {result.scan_duration_seconds:.2f} seconds",
        f"Files scanned: {result.files_scanned}",
        f"Directories scanned: {result.directories_scanned}",
        f"Secrets found: {len(result.secrets)}",
        "",
    ]

    if result.secrets:
        lines.append("-" * 60)
        lines.append("DISCOVERED SECRETS")
        lines.append("-" * 60)

        # Group by type
        by_type: dict[SecretType, list[SecretMatch]] = {}
        for secret in result.secrets:
            if secret.secret_type not in by_type:
                by_type[secret.secret_type] = []
            by_type[secret.secret_type].append(secret)

        for secret_type, secrets in sorted(by_type.items(), key=lambda x: x[0].value):
            lines.append(f"\n[{secret_type.value.upper()}] ({len(secrets)} found)")
            for secret in secrets:
                suggested_name = suggest_key_name(secret)
                in_store = "[OK] IN STORE" if suggested_name in existing_keys else "[--] NOT IN STORE"
                lines.append(f"  * {secret.masked_value}")
                lines.append(f"    Location: {secret.location}" + (f":{secret.line_number}" if secret.line_number else ""))
                lines.append(f"    Confidence: {secret.confidence:.0%}")
                lines.append(f"    Suggested name: {suggested_name} [{in_store}]")

    # Keys in store but not found in scan
    lines.append("")
    lines.append("-" * 60)
    lines.append("CREDENTIAL STORE STATUS")
    lines.append("-" * 60)

    found_names = {suggest_key_name(s) for s in result.secrets}
    for key_name, masked_value in sorted(existing_keys.items()):
        status = "[OK] Found in scan" if key_name in found_names else "[??] Not found in scan"
        lines.append(f"  {key_name}: {masked_value} [{status}]")

    if result.errors:
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"ERRORS ({len(result.errors)})")
        lines.append("-" * 60)
        for error in result.errors[:10]:  # Show first 10
            lines.append(f"  * {error}")
        if len(result.errors) > 10:
            lines.append(f"  ... and {len(result.errors) - 10} more")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def export_to_env_template(
    secrets: list[SecretMatch],
    include_values: bool = False,
) -> str:
    """Export discovered secrets as an .env template."""
    lines = [
        "# Discovered secrets - generated by secrets_scanner",
        f"# Generated: {datetime.now().isoformat()}",
        "",
    ]

    seen_names = set()
    for secret in secrets:
        name = suggest_key_name(secret)
        if name in seen_names:
            continue
        seen_names.add(name)

        if include_values:
            lines.append(f"{name}={secret.value}")
        else:
            lines.append(f"{name}=  # {secret.secret_type.value}")

    return "\n".join(lines)
