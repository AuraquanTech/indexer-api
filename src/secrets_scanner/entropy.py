"""
Entropy-based secret detection.
High entropy strings are often secrets (random API keys, passwords, etc.)
"""
import math
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class EntropyResult:
    """Result of entropy analysis on a string."""
    value: str
    entropy: float
    is_high_entropy: bool
    charset_type: str  # "hex", "base64", "alphanumeric", "mixed"
    length: int
    confidence: float


# Character sets for entropy calculation
CHARSETS = {
    "hex": "0123456789abcdefABCDEF",
    "base64": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
    "base64url": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
    "alphanumeric": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
    "numeric": "0123456789",
}

# Entropy thresholds for different character sets
ENTROPY_THRESHOLDS = {
    "hex": 3.0,          # Hex has lower max entropy
    "base64": 4.5,       # Base64 is denser
    "base64url": 4.5,
    "alphanumeric": 4.0,
    "mixed": 4.5,
    "numeric": 2.5,
}

# Minimum length for entropy-based detection
MIN_LENGTH_FOR_ENTROPY = 16

# Words/patterns to exclude (common false positives)
ENTROPY_EXCLUDE_PATTERNS = [
    re.compile(r'^[a-f0-9]{32}$'),  # Could be MD5 hash (file hash, not secret)
    re.compile(r'^[a-f0-9]{40}$'),  # Could be SHA1 hash
    re.compile(r'^[a-f0-9]{64}$'),  # Could be SHA256 hash
    re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),  # UUID
    re.compile(r'placeholder|example|sample|test|dummy|fake|mock', re.I),
]


def calculate_shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0

    # Count character frequencies
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1

    # Calculate entropy
    length = len(s)
    entropy = 0.0
    for count in freq.values():
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)

    return entropy


def detect_charset(s: str) -> str:
    """Detect which character set a string belongs to."""
    if all(c in CHARSETS["numeric"] for c in s):
        return "numeric"
    if all(c in CHARSETS["hex"] for c in s):
        return "hex"
    if all(c in CHARSETS["base64url"] for c in s):
        return "base64url"
    if all(c in CHARSETS["base64"] for c in s):
        return "base64"
    if all(c in CHARSETS["alphanumeric"] + "_-" for c in s):
        return "alphanumeric"
    return "mixed"


def is_excluded(s: str) -> bool:
    """Check if string matches exclusion patterns (likely false positive)."""
    for pattern in ENTROPY_EXCLUDE_PATTERNS:
        if pattern.match(s):
            return True
    return False


def analyze_entropy(value: str, context: Optional[str] = None) -> EntropyResult:
    """
    Analyze a string for high entropy (potential secret).

    Args:
        value: The string to analyze
        context: Optional surrounding context (variable name, etc.)

    Returns:
        EntropyResult with analysis
    """
    entropy = calculate_shannon_entropy(value)
    charset = detect_charset(value)
    threshold = ENTROPY_THRESHOLDS.get(charset, 4.0)

    is_high = (
        entropy >= threshold
        and len(value) >= MIN_LENGTH_FOR_ENTROPY
        and not is_excluded(value)
    )

    # Calculate confidence based on multiple factors
    confidence = 0.0
    if is_high:
        # Base confidence from entropy ratio
        confidence = min((entropy / threshold) * 0.5, 0.5)

        # Boost for certain lengths (common key lengths)
        if len(value) in [32, 36, 40, 48, 64, 128]:
            confidence += 0.15

        # Boost for context suggesting it's a secret
        if context:
            secret_context_patterns = [
                r'(?i)key', r'(?i)token', r'(?i)secret', r'(?i)password',
                r'(?i)credential', r'(?i)auth', r'(?i)api', r'(?i)private'
            ]
            for pattern in secret_context_patterns:
                if re.search(pattern, context):
                    confidence += 0.1
                    break

        # Reduce confidence for certain patterns
        if charset == "numeric":
            confidence -= 0.2  # Numbers alone are less likely to be secrets

        confidence = max(0.0, min(1.0, confidence))

    return EntropyResult(
        value=value,
        entropy=entropy,
        is_high_entropy=is_high,
        charset_type=charset,
        length=len(value),
        confidence=confidence if is_high else 0.0
    )


def extract_high_entropy_strings(
    text: str,
    min_length: int = MIN_LENGTH_FOR_ENTROPY,
    min_confidence: float = 0.3
) -> list[tuple[str, EntropyResult]]:
    """
    Extract all high-entropy strings from text.

    Args:
        text: The text to analyze
        min_length: Minimum string length to consider
        min_confidence: Minimum confidence threshold

    Returns:
        List of (matched_string, EntropyResult) tuples
    """
    results = []

    # Pattern to find potential secrets (quoted strings, assignments)
    patterns = [
        # Quoted strings
        (r'["\']([A-Za-z0-9_+/=-]{' + str(min_length) + r',})["\']', None),
        # Env var style
        (r'([A-Z_]+)\s*=\s*([A-Za-z0-9_+/=-]{' + str(min_length) + r',})', 0),
        # JSON/YAML style
        (r'["\']?([a-zA-Z_]+)["\']?\s*:\s*["\']?([A-Za-z0-9_+/=-]{' + str(min_length) + r',})["\']?', 0),
    ]

    for pattern, context_group in patterns:
        for match in re.finditer(pattern, text):
            if context_group is not None:
                context = match.group(1)
                value = match.group(2)
            else:
                context = None
                value = match.group(1)

            result = analyze_entropy(value, context)
            if result.is_high_entropy and result.confidence >= min_confidence:
                results.append((value, result))

    # Deduplicate
    seen = set()
    unique_results = []
    for value, result in results:
        if value not in seen:
            seen.add(value)
            unique_results.append((value, result))

    return unique_results


def get_max_entropy(charset: str) -> float:
    """Get the maximum possible entropy for a character set."""
    chars = CHARSETS.get(charset, "")
    if not chars:
        return 8.0  # Assume full ASCII
    return math.log2(len(set(chars)))
