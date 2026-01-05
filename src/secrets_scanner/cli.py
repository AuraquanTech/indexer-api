#!/usr/bin/env python3
"""
Command-line interface for the secrets scanner.

Usage:
    python -m secrets_scanner scan [paths...]
    python -m secrets_scanner scan --env --cloud --registry
    python -m secrets_scanner report
    python -m secrets_scanner add-to-store [--all] [--interactive]
"""
import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .scanner import SecretsScanner, ScanResult
from .integrations import (
    generate_report,
    get_existing_keys,
    add_to_credentials_store,
    batch_add_to_credentials,
    export_to_env_template,
    CredentialStoreConfig,
)
from .patterns import SecretType


def progress_callback(file_path: str, current: int, total: int):
    """Display scan progress."""
    pct = (current / total) * 100 if total > 0 else 0
    bar_width = 30
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)
    print(f"\r  [{bar}] {pct:5.1f}% ({current}/{total}) {Path(file_path).name[:30]:<30}", end="", flush=True)


def cmd_scan(args):
    """Run a secrets scan."""
    print("=" * 60)
    print("SECRETS SCANNER")
    print("=" * 60)

    scanner = SecretsScanner(
        min_confidence=args.min_confidence,
        use_entropy=not args.no_entropy,
        entropy_min_confidence=args.entropy_confidence,
        max_workers=args.workers,
        progress_callback=progress_callback if not args.quiet else None,
    )

    # Determine what to scan
    directories = []
    if args.paths:
        directories = [Path(p) for p in args.paths]
    elif args.home:
        directories = [Path.home()]

    # Default to common project locations
    if not directories and not args.env and not args.cloud and not args.registry:
        # Scan current directory by default
        directories = [Path.cwd()]

    print(f"\nScan configuration:")
    print(f"  Directories: {[str(d) for d in directories] if directories else 'None'}")
    print(f"  Environment variables: {args.env}")
    print(f"  Cloud configs: {args.cloud}")
    print(f"  Windows registry: {args.registry}")
    print(f"  Git history: {args.git}")
    print(f"  Min confidence: {args.min_confidence}")
    print(f"  Entropy detection: {not args.no_entropy}")
    print()

    # Run scan
    if not args.quiet:
        print("Scanning...")

    result = scanner.full_scan(
        directories=directories if directories else None,
        scan_env=args.env,
        scan_cloud=args.cloud,
        scan_registry=args.registry,
        scan_git=args.git,
        git_repos=directories if args.git else None,
    )

    if not args.quiet:
        print("\n")  # Clear progress line

    # Output results
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        existing = get_existing_keys() if not args.no_store_check else {}
        report = generate_report(result, existing)
        print(report)

    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        if args.format == "json":
            with open(output_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
        else:
            with open(output_path, 'w') as f:
                f.write(generate_report(result))
        print(f"\nResults saved to: {output_path}")

    # Interactive add to store
    if args.add_to_store and result.secrets:
        print("\n" + "=" * 60)
        print("ADD TO CREDENTIAL STORE")
        print("=" * 60)

        if args.interactive:
            results = batch_add_to_credentials(
                result.secrets,
                overwrite=args.overwrite,
                interactive=True,
            )
        else:
            # Add all automatically
            results = batch_add_to_credentials(
                result.secrets,
                overwrite=args.overwrite,
                interactive=False,
            )

        # Show results
        added = sum(1 for _, success, _ in results if success)
        print(f"\nAdded {added}/{len(results)} secrets to credential store")

    return 0 if not result.errors else 1


def cmd_report(args):
    """Show current credential store status."""
    config = CredentialStoreConfig()

    if not config.credentials_dir.exists():
        print(f"Credential store not found at: {config.credentials_dir}")
        print("Run the scan command first to discover secrets.")
        return 1

    existing = get_existing_keys(config)

    print("=" * 60)
    print("CREDENTIAL STORE CONTENTS")
    print("=" * 60)
    print(f"Location: {config.env_file}")
    print(f"Keys stored: {len(existing)}")
    print()

    if existing:
        for name, masked in sorted(existing.items()):
            print(f"  [{name}] = {masked}")
    else:
        print("  (no keys stored)")

    return 0


def cmd_add(args):
    """Manually add a secret to the store."""
    from getpass import getpass

    key_name = args.name.upper().replace("-", "_")

    if args.value:
        value = args.value
    else:
        value = getpass(f"Enter value for {key_name}: ")

    if not value:
        print("No value provided, aborting.")
        return 1

    # Create a mock SecretMatch
    from .scanner import SecretMatch, ScanSource

    secret = SecretMatch(
        secret_type=SecretType.API_KEY_GENERIC,
        value=value,
        masked_value="****",
        source=ScanSource.FILE,
        location="manual entry",
    )

    success, message = add_to_credentials_store(
        secret,
        key_name=key_name,
        overwrite=args.overwrite,
    )

    if success:
        print(f"[OK] {message}")
        return 0
    else:
        print(f"[FAIL] {message}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Secrets Scanner - Find and manage exposed secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory
  python -m secrets_scanner scan

  # Scan specific paths
  python -m secrets_scanner scan /path/to/project1 /path/to/project2

  # Scan environment, cloud configs, and registry
  python -m secrets_scanner scan --env --cloud --registry

  # Scan everything on home directory
  python -m secrets_scanner scan --home --env --cloud --registry

  # Scan and add to credential store
  python -m secrets_scanner scan --add-to-store --interactive

  # Show credential store status
  python -m secrets_scanner report
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for secrets")
    scan_parser.add_argument("paths", nargs="*", help="Paths to scan")
    scan_parser.add_argument("--home", action="store_true", help="Scan home directory")
    scan_parser.add_argument("--env", action="store_true", help="Scan environment variables")
    scan_parser.add_argument("--cloud", action="store_true", help="Scan cloud provider configs")
    scan_parser.add_argument("--registry", action="store_true", help="Scan Windows registry")
    scan_parser.add_argument("--git", action="store_true", help="Scan git history")
    scan_parser.add_argument("--no-entropy", action="store_true", help="Disable entropy-based detection")
    scan_parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence threshold")
    scan_parser.add_argument("--entropy-confidence", type=float, default=0.4, help="Minimum entropy confidence")
    scan_parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    scan_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    scan_parser.add_argument("--output", "-o", help="Save results to file")
    scan_parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    scan_parser.add_argument("--add-to-store", action="store_true", help="Add found secrets to credential store")
    scan_parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode for adding secrets")
    scan_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing keys in store")
    scan_parser.add_argument("--no-store-check", action="store_true", help="Don't check credential store status")
    scan_parser.set_defaults(func=cmd_scan)

    # Report command
    report_parser = subparsers.add_parser("report", help="Show credential store status")
    report_parser.set_defaults(func=cmd_report)

    # Add command
    add_parser = subparsers.add_parser("add", help="Manually add a secret")
    add_parser.add_argument("name", help="Key name")
    add_parser.add_argument("--value", help="Secret value (will prompt if not provided)")
    add_parser.add_argument("--overwrite", action="store_true", help="Overwrite if exists")
    add_parser.set_defaults(func=cmd_add)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
