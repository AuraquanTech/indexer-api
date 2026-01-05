"""
Main secrets scanner - orchestrates pattern and entropy-based detection.
Supports local files, git repos, cloud configs, and environment variables.
"""
import os
import re
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Iterator, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from .patterns import SECRET_PATTERNS, SecretPattern, SecretType, get_env_var_name
from .entropy import analyze_entropy, extract_high_entropy_strings, EntropyResult


class ScanSource(str, Enum):
    """Source types for secret detection."""
    FILE = "file"
    GIT_HISTORY = "git_history"
    ENV_VAR = "environment_variable"
    CLOUD_CONFIG = "cloud_config"
    CLIPBOARD = "clipboard"
    REGISTRY = "windows_registry"


@dataclass
class SecretMatch:
    """A detected secret."""
    secret_type: SecretType
    value: str
    masked_value: str
    source: ScanSource
    location: str  # File path, env var name, etc.
    line_number: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None  # Surrounding code/text
    confidence: float = 0.0
    pattern_name: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    is_entropy_based: bool = False

    def to_dict(self) -> dict:
        return {
            "secret_type": self.secret_type.value,
            "masked_value": self.masked_value,
            "source": self.source.value,
            "location": self.location,
            "line_number": self.line_number,
            "confidence": self.confidence,
            "pattern_name": self.pattern_name,
            "detected_at": self.detected_at.isoformat(),
            "is_entropy_based": self.is_entropy_based,
        }


@dataclass
class ScanResult:
    """Results from a scan operation."""
    secrets: list[SecretMatch] = field(default_factory=list)
    files_scanned: int = 0
    directories_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    scan_duration_seconds: float = 0.0
    scan_started: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "secrets_found": len(self.secrets),
            "files_scanned": self.files_scanned,
            "directories_scanned": self.directories_scanned,
            "errors": self.errors,
            "scan_duration_seconds": self.scan_duration_seconds,
            "secrets": [s.to_dict() for s in self.secrets],
        }


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret value for safe display."""
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return f"{value[:visible_chars]}{'*' * 4}{value[-visible_chars:]}"


# Files that commonly contain secrets
SECRET_FILE_PATTERNS = [
    ".env", ".env.*", "*.env",
    ".envrc",
    "credentials", "credentials.*",
    "secrets.*", "*.secret", "*.secrets",
    "config.json", "config.yaml", "config.yml", "config.toml",
    "settings.json", "settings.yaml", "settings.yml",
    "application.properties", "application.yml",
    ".npmrc", ".pypirc", ".netrc", ".docker/config.json",
    "docker-compose*.yml", "docker-compose*.yaml",
    ".aws/credentials", ".aws/config",
    ".kube/config", "kubeconfig*",
    "*.pem", "*.key", "*.p12", "*.pfx",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    ".htpasswd", ".htaccess",
    "wp-config.php",
    "database.yml", "database.json",
    "appsettings.json", "appsettings.*.json",
    "terraform.tfvars", "*.auto.tfvars",
    "ansible-vault*", "vault.yml",
    ".git-credentials",
    "service-account*.json", "*-credentials.json",
]

# Directories to skip
SKIP_DIRECTORIES = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "env", ".env",
    ".tox", ".nox",
    "dist", "build", "target",
    ".idea", ".vscode",
    "vendor", "packages",
    ".cache", "cache",
}

# File extensions to scan
SCANNABLE_EXTENSIONS = {
    ".env", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".properties", ".xml", ".config",
    ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".java", ".kt", ".scala", ".groovy",
    ".go", ".rs", ".rb", ".php",
    ".cs", ".fs", ".vb",
    ".c", ".cpp", ".h", ".hpp",
    ".swift", ".m", ".mm",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1", ".bat", ".cmd",
    ".sql", ".graphql",
    ".tf", ".hcl",
    ".dockerfile", ".docker",
    ".md", ".txt", ".rst",  # Documentation might contain examples
    ".pem", ".key", ".crt", ".cer",
}


class SecretsScanner:
    """
    Multi-source secrets scanner with pattern and entropy detection.
    """

    def __init__(
        self,
        patterns: list[SecretPattern] = None,
        min_confidence: float = 0.5,
        use_entropy: bool = True,
        entropy_min_confidence: float = 0.4,
        max_file_size_mb: float = 10.0,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        self.patterns = patterns or SECRET_PATTERNS
        self.min_confidence = min_confidence
        self.use_entropy = use_entropy
        self.entropy_min_confidence = entropy_min_confidence
        self.max_file_size = int(max_file_size_mb * 1024 * 1024)
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self._seen_secrets: set[str] = set()

    def scan_text(
        self,
        text: str,
        source: ScanSource = ScanSource.FILE,
        location: str = "<unknown>",
    ) -> list[SecretMatch]:
        """Scan a text string for secrets."""
        matches = []

        # Pattern-based detection
        for pattern in self.patterns:
            for match in pattern.pattern.finditer(text):
                # Get the actual secret value
                if match.groups():
                    value = match.group(1)
                else:
                    value = match.group(0)

                # Skip if we've seen this exact secret
                if value in self._seen_secrets:
                    continue

                # Validate if validator exists
                if pattern.validator and not pattern.validator(value):
                    continue

                # Calculate line number
                line_num = text[:match.start()].count('\n') + 1

                # Get context
                lines = text.split('\n')
                if 0 < line_num <= len(lines):
                    context = lines[line_num - 1].strip()[:200]
                else:
                    context = None

                if pattern.confidence >= self.min_confidence:
                    self._seen_secrets.add(value)
                    matches.append(SecretMatch(
                        secret_type=pattern.secret_type,
                        value=value,
                        masked_value=mask_secret(value),
                        source=source,
                        location=location,
                        line_number=line_num,
                        context=context,
                        confidence=pattern.confidence,
                        pattern_name=pattern.name,
                    ))

        # Entropy-based detection
        if self.use_entropy:
            for value, entropy_result in extract_high_entropy_strings(
                text,
                min_confidence=self.entropy_min_confidence
            ):
                if value in self._seen_secrets:
                    continue

                # Find line number
                idx = text.find(value)
                line_num = text[:idx].count('\n') + 1 if idx >= 0 else None

                if entropy_result.confidence >= self.entropy_min_confidence:
                    self._seen_secrets.add(value)
                    matches.append(SecretMatch(
                        secret_type=SecretType.API_KEY_GENERIC,
                        value=value,
                        masked_value=mask_secret(value),
                        source=source,
                        location=location,
                        line_number=line_num,
                        confidence=entropy_result.confidence,
                        pattern_name=f"High entropy ({entropy_result.entropy:.2f})",
                        is_entropy_based=True,
                    ))

        return matches

    def scan_file(self, file_path: Path) -> list[SecretMatch]:
        """Scan a single file for secrets."""
        try:
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return []

            # Read file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except (IOError, OSError):
                return []

            return self.scan_text(content, ScanSource.FILE, str(file_path))

        except Exception as e:
            return []

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        include_patterns: list[str] = None,
        exclude_patterns: list[str] = None,
    ) -> ScanResult:
        """Scan a directory for secrets."""
        import time
        start_time = time.time()
        result = ScanResult()

        # Collect files to scan
        files_to_scan = []
        for root, dirs, files in os.walk(directory):
            result.directories_scanned += 1

            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]

            for file in files:
                file_path = Path(root) / file

                # Check if file matches patterns
                if include_patterns:
                    if not any(file_path.match(p) for p in include_patterns):
                        continue
                else:
                    # Use default extension filter
                    if file_path.suffix.lower() not in SCANNABLE_EXTENSIONS:
                        # Check for special filenames
                        if not any(file_path.match(p) for p in SECRET_FILE_PATTERNS):
                            continue

                if exclude_patterns:
                    if any(file_path.match(p) for p in exclude_patterns):
                        continue

                files_to_scan.append(file_path)

            if not recursive:
                break

        # Scan files in parallel
        total_files = len(files_to_scan)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_file, f): f for f in files_to_scan}

            for i, future in enumerate(as_completed(futures)):
                file_path = futures[future]
                try:
                    matches = future.result()
                    result.secrets.extend(matches)
                    result.files_scanned += 1

                    if self.progress_callback:
                        self.progress_callback(str(file_path), i + 1, total_files)
                except Exception as e:
                    result.errors.append(f"{file_path}: {e}")

        result.scan_duration_seconds = time.time() - start_time
        return result

    def scan_environment(self) -> list[SecretMatch]:
        """Scan environment variables for secrets."""
        matches = []
        for name, value in os.environ.items():
            if not value or len(value) < 8:
                continue

            # Scan the value
            text_matches = self.scan_text(
                value,
                ScanSource.ENV_VAR,
                f"${name}"
            )
            matches.extend(text_matches)

            # Also check if the env var name suggests it's a secret
            secret_name_patterns = [
                r'(?i)key', r'(?i)token', r'(?i)secret', r'(?i)password',
                r'(?i)credential', r'(?i)auth', r'(?i)api',
            ]
            if any(re.search(p, name) for p in secret_name_patterns):
                # Check entropy even if pattern didn't match
                if value not in self._seen_secrets:
                    entropy = analyze_entropy(value, name)
                    if entropy.is_high_entropy and entropy.confidence > 0.3:
                        self._seen_secrets.add(value)
                        matches.append(SecretMatch(
                            secret_type=SecretType.API_KEY_GENERIC,
                            value=value,
                            masked_value=mask_secret(value),
                            source=ScanSource.ENV_VAR,
                            location=f"${name}",
                            confidence=entropy.confidence,
                            pattern_name=f"Env var with secret name (entropy: {entropy.entropy:.2f})",
                            is_entropy_based=True,
                        ))

        return matches

    def scan_git_history(
        self,
        repo_path: Path,
        max_commits: int = 100,
    ) -> list[SecretMatch]:
        """Scan git history for secrets."""
        matches = []

        try:
            # Get list of commits
            result = subprocess.run(
                ["git", "log", f"--max-count={max_commits}", "--pretty=format:%H"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return matches

            commits = result.stdout.strip().split('\n')

            for commit in commits:
                if not commit:
                    continue

                # Get diff for this commit
                diff_result = subprocess.run(
                    ["git", "show", commit, "--pretty=format:", "--name-only"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if diff_result.returncode != 0:
                    continue

                # Scan the diff
                commit_matches = self.scan_text(
                    diff_result.stdout,
                    ScanSource.GIT_HISTORY,
                    f"git:{commit[:8]}"
                )
                for m in commit_matches:
                    m.context = f"Commit: {commit[:8]}"
                matches.extend(commit_matches)

        except FileNotFoundError:
            # Git not installed
            pass

        return matches

    def scan_cloud_configs(self, home_dir: Path = None) -> list[SecretMatch]:
        """Scan cloud provider configuration files."""
        if home_dir is None:
            home_dir = Path.home()

        matches = []

        # Cloud config locations
        cloud_configs = [
            # AWS
            home_dir / ".aws" / "credentials",
            home_dir / ".aws" / "config",
            # GCP
            home_dir / ".config" / "gcloud" / "credentials.db",
            home_dir / ".config" / "gcloud" / "application_default_credentials.json",
            # Azure
            home_dir / ".azure" / "credentials",
            home_dir / ".azure" / "accessTokens.json",
            # Kubernetes
            home_dir / ".kube" / "config",
            # Docker
            home_dir / ".docker" / "config.json",
            # Terraform
            home_dir / ".terraform.d" / "credentials.tfrc.json",
            # NPM
            home_dir / ".npmrc",
            # PyPI
            home_dir / ".pypirc",
            # Git credentials
            home_dir / ".git-credentials",
            # Netlify
            home_dir / ".netlify" / "config.json",
            # Vercel
            home_dir / ".vercel" / "auth.json",
            # Heroku
            home_dir / ".netrc",
            # SSH keys
            home_dir / ".ssh" / "id_rsa",
            home_dir / ".ssh" / "id_ed25519",
            home_dir / ".ssh" / "id_ecdsa",
            # Supabase
            home_dir / ".supabase" / "access-token",
        ]

        for config_path in cloud_configs:
            if config_path.exists() and config_path.is_file():
                file_matches = self.scan_file(config_path)
                for m in file_matches:
                    m.source = ScanSource.CLOUD_CONFIG
                matches.extend(file_matches)

        return matches

    def scan_windows_registry(self) -> list[SecretMatch]:
        """Scan Windows registry for stored secrets (Windows only)."""
        matches = []

        if os.name != 'nt':
            return matches

        try:
            import winreg

            # Common registry locations for secrets
            registry_paths = [
                (winreg.HKEY_CURRENT_USER, r"Environment"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU"),
            ]

            for hkey, subkey in registry_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                if isinstance(value, str) and len(value) >= 8:
                                    reg_matches = self.scan_text(
                                        value,
                                        ScanSource.REGISTRY,
                                        f"HKCU\\{subkey}\\{name}"
                                    )
                                    matches.extend(reg_matches)
                                i += 1
                            except OSError:
                                break
                except (OSError, PermissionError):
                    pass

        except ImportError:
            pass

        return matches

    def full_scan(
        self,
        directories: list[Path] = None,
        scan_env: bool = True,
        scan_cloud: bool = True,
        scan_registry: bool = True,
        scan_git: bool = False,
        git_repos: list[Path] = None,
    ) -> ScanResult:
        """Perform a comprehensive scan."""
        import time
        start_time = time.time()
        result = ScanResult()

        # Scan directories
        if directories:
            for directory in directories:
                if directory.exists():
                    dir_result = self.scan_directory(directory)
                    result.secrets.extend(dir_result.secrets)
                    result.files_scanned += dir_result.files_scanned
                    result.directories_scanned += dir_result.directories_scanned
                    result.errors.extend(dir_result.errors)

        # Scan environment variables
        if scan_env:
            env_matches = self.scan_environment()
            result.secrets.extend(env_matches)

        # Scan cloud configs
        if scan_cloud:
            cloud_matches = self.scan_cloud_configs()
            result.secrets.extend(cloud_matches)

        # Scan Windows registry
        if scan_registry and os.name == 'nt':
            reg_matches = self.scan_windows_registry()
            result.secrets.extend(reg_matches)

        # Scan git history
        if scan_git and git_repos:
            for repo in git_repos:
                git_matches = self.scan_git_history(repo)
                result.secrets.extend(git_matches)

        result.scan_duration_seconds = time.time() - start_time
        return result
