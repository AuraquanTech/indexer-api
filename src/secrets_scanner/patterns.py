"""
Secret detection patterns - regex patterns for known API key formats.
Each pattern includes metadata for classification and validation.
"""
import re
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class SecretType(str, Enum):
    # AI/ML Services
    OPENAI = "openai_api_key"
    ANTHROPIC = "anthropic_api_key"
    HUGGINGFACE = "huggingface_token"
    REPLICATE = "replicate_api_token"
    COHERE = "cohere_api_key"
    PERPLEXITY = "perplexity_api_key"
    GOOGLE_AI = "google_ai_api_key"
    AZURE_OPENAI = "azure_openai_key"

    # Cloud Providers
    AWS_ACCESS_KEY = "aws_access_key_id"
    AWS_SECRET_KEY = "aws_secret_access_key"
    AZURE_SUBSCRIPTION = "azure_subscription_key"
    GCP_API_KEY = "gcp_api_key"
    GCP_SERVICE_ACCOUNT = "gcp_service_account"
    DIGITALOCEAN = "digitalocean_token"
    LINODE = "linode_api_token"
    VULTR = "vultr_api_key"

    # Code/DevOps
    GITHUB_TOKEN = "github_token"
    GITHUB_PAT = "github_pat"
    GITLAB_TOKEN = "gitlab_token"
    BITBUCKET_TOKEN = "bitbucket_token"
    NPM_TOKEN = "npm_token"
    PYPI_TOKEN = "pypi_token"
    DOCKER_HUB = "docker_hub_token"
    CIRCLECI = "circleci_token"
    TRAVIS_CI = "travis_ci_token"

    # Databases
    DATABASE_URL = "database_url"
    MONGODB_URI = "mongodb_uri"
    REDIS_URL = "redis_url"
    POSTGRES_PASSWORD = "postgres_password"
    MYSQL_PASSWORD = "mysql_password"
    SUPABASE_KEY = "supabase_key"
    FIREBASE_KEY = "firebase_key"

    # Payment/Finance
    STRIPE_KEY = "stripe_api_key"
    STRIPE_SECRET = "stripe_secret_key"
    PAYPAL_CLIENT = "paypal_client_id"
    SQUARE_TOKEN = "square_access_token"
    PLAID_KEY = "plaid_api_key"

    # Communication
    TWILIO_SID = "twilio_account_sid"
    TWILIO_TOKEN = "twilio_auth_token"
    SENDGRID = "sendgrid_api_key"
    MAILGUN = "mailgun_api_key"
    SLACK_TOKEN = "slack_token"
    SLACK_WEBHOOK = "slack_webhook"
    DISCORD_TOKEN = "discord_token"
    DISCORD_WEBHOOK = "discord_webhook"
    TELEGRAM_TOKEN = "telegram_bot_token"

    # Social/APIs
    TWITTER_KEY = "twitter_api_key"
    FACEBOOK_TOKEN = "facebook_access_token"
    INSTAGRAM_TOKEN = "instagram_access_token"
    LINKEDIN_TOKEN = "linkedin_access_token"
    GOOGLE_OAUTH = "google_oauth_secret"

    # Storage/CDN
    CLOUDFLARE_KEY = "cloudflare_api_key"
    CLOUDINARY_KEY = "cloudinary_api_key"
    S3_BUCKET_KEY = "s3_bucket_key"

    # Misc
    JWT_SECRET = "jwt_secret"
    PRIVATE_KEY = "private_key"
    SSH_KEY = "ssh_private_key"
    ENCRYPTION_KEY = "encryption_key"
    API_KEY_GENERIC = "generic_api_key"
    PASSWORD = "password"
    SECRET = "secret"
    NOTION = "notion_api_key"
    AIRTABLE = "airtable_api_key"
    ZAPIER = "zapier_webhook"
    WEBHOOK_SECRET = "webhook_secret"
    BRAVE_SEARCH = "brave_search_api_key"


@dataclass
class SecretPattern:
    """Defines a pattern for detecting a specific type of secret."""
    name: str
    secret_type: SecretType
    pattern: re.Pattern
    description: str
    confidence: float  # 0.0 to 1.0
    validator: Optional[Callable[[str], bool]] = None
    env_var_names: tuple = ()  # Common environment variable names


# Validation functions
def validate_luhn(s: str) -> bool:
    """Luhn checksum validation for certain keys."""
    try:
        digits = [int(d) for d in s if d.isdigit()]
        checksum = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0
    except:
        return True  # Don't invalidate if we can't check


def validate_base64(s: str) -> bool:
    """Check if string is valid base64."""
    import base64
    try:
        base64.b64decode(s)
        return True
    except:
        return False


def validate_jwt(s: str) -> bool:
    """Check if string looks like a JWT."""
    parts = s.split('.')
    return len(parts) == 3 and all(len(p) > 10 for p in parts)


# =============================================================================
# SECRET PATTERNS DATABASE
# =============================================================================

SECRET_PATTERNS: list[SecretPattern] = [
    # -------------------------------------------------------------------------
    # AI/ML Services
    # -------------------------------------------------------------------------
    SecretPattern(
        name="OpenAI API Key",
        secret_type=SecretType.OPENAI,
        pattern=re.compile(r'sk-(?:proj-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,}'),
        description="OpenAI API key (sk-... format)",
        confidence=0.95,
        env_var_names=("OPENAI_API_KEY", "OPENAI_KEY"),
    ),
    SecretPattern(
        name="OpenAI API Key (legacy)",
        secret_type=SecretType.OPENAI,
        pattern=re.compile(r'sk-[A-Za-z0-9]{48}'),
        description="OpenAI API key legacy format",
        confidence=0.90,
        env_var_names=("OPENAI_API_KEY",),
    ),
    SecretPattern(
        name="Anthropic API Key",
        secret_type=SecretType.ANTHROPIC,
        pattern=re.compile(r'sk-ant-api\d{2}-[A-Za-z0-9_-]{93}'),
        description="Anthropic Claude API key",
        confidence=0.98,
        env_var_names=("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    ),
    SecretPattern(
        name="HuggingFace Token",
        secret_type=SecretType.HUGGINGFACE,
        pattern=re.compile(r'hf_[A-Za-z0-9]{34,}'),
        description="HuggingFace API token",
        confidence=0.95,
        env_var_names=("HUGGINGFACE_TOKEN", "HF_TOKEN", "HUGGINGFACE_API_KEY"),
    ),
    SecretPattern(
        name="Replicate API Token",
        secret_type=SecretType.REPLICATE,
        pattern=re.compile(r'r8_[A-Za-z0-9]{37}'),
        description="Replicate API token",
        confidence=0.95,
        env_var_names=("REPLICATE_API_TOKEN",),
    ),
    SecretPattern(
        name="Perplexity API Key",
        secret_type=SecretType.PERPLEXITY,
        pattern=re.compile(r'pplx-[A-Za-z0-9]{48,}'),
        description="Perplexity AI API key",
        confidence=0.95,
        env_var_names=("PERPLEXITY_API_KEY",),
    ),
    SecretPattern(
        name="Cohere API Key",
        secret_type=SecretType.COHERE,
        pattern=re.compile(r'(?i)(?:cohere_api_key|cohere_key)["\s:=]+["\']?([A-Za-z0-9]{40})["\']?'),
        description="Cohere API key (context-required)",
        confidence=0.85,
        env_var_names=("COHERE_API_KEY",),
    ),

    # -------------------------------------------------------------------------
    # Cloud Providers
    # -------------------------------------------------------------------------
    SecretPattern(
        name="AWS Access Key ID",
        secret_type=SecretType.AWS_ACCESS_KEY,
        pattern=re.compile(r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'),
        description="AWS Access Key ID",
        confidence=0.95,
        env_var_names=("AWS_ACCESS_KEY_ID", "AWS_ACCESS_KEY"),
    ),
    SecretPattern(
        name="AWS Secret Access Key",
        secret_type=SecretType.AWS_SECRET_KEY,
        pattern=re.compile(r'(?i)(?:aws_secret_access_key|aws_secret_key)["\s:=]+["\']?([A-Za-z0-9/+=]{40})["\']?'),
        description="AWS Secret Access Key",
        confidence=0.90,
        env_var_names=("AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY"),
    ),
    SecretPattern(
        name="Google Cloud API Key",
        secret_type=SecretType.GCP_API_KEY,
        pattern=re.compile(r'AIza[A-Za-z0-9_-]{35}'),
        description="Google Cloud/Firebase API key",
        confidence=0.95,
        env_var_names=("GOOGLE_API_KEY", "GCP_API_KEY", "FIREBASE_API_KEY"),
    ),
    SecretPattern(
        name="GCP Service Account",
        secret_type=SecretType.GCP_SERVICE_ACCOUNT,
        pattern=re.compile(r'"type"\s*:\s*"service_account"'),
        description="GCP Service Account JSON",
        confidence=0.98,
        env_var_names=("GOOGLE_APPLICATION_CREDENTIALS",),
    ),
    SecretPattern(
        name="Azure Subscription Key",
        secret_type=SecretType.AZURE_SUBSCRIPTION,
        pattern=re.compile(r'[a-f0-9]{32}'),  # Generic, needs context
        description="Azure subscription key",
        confidence=0.4,
        env_var_names=("AZURE_SUBSCRIPTION_KEY", "AZURE_API_KEY"),
    ),
    SecretPattern(
        name="DigitalOcean Token",
        secret_type=SecretType.DIGITALOCEAN,
        pattern=re.compile(r'dop_v1_[a-f0-9]{64}'),
        description="DigitalOcean personal access token",
        confidence=0.98,
        env_var_names=("DIGITALOCEAN_TOKEN", "DO_API_TOKEN"),
    ),

    # -------------------------------------------------------------------------
    # Code/DevOps
    # -------------------------------------------------------------------------
    SecretPattern(
        name="GitHub Personal Access Token",
        secret_type=SecretType.GITHUB_PAT,
        pattern=re.compile(r'ghp_[A-Za-z0-9]{36}'),
        description="GitHub personal access token",
        confidence=0.98,
        env_var_names=("GITHUB_TOKEN", "GITHUB_PAT", "GH_TOKEN"),
    ),
    SecretPattern(
        name="GitHub OAuth Token",
        secret_type=SecretType.GITHUB_TOKEN,
        pattern=re.compile(r'gho_[A-Za-z0-9]{36}'),
        description="GitHub OAuth access token",
        confidence=0.98,
        env_var_names=("GITHUB_OAUTH_TOKEN",),
    ),
    SecretPattern(
        name="GitHub App Token",
        secret_type=SecretType.GITHUB_TOKEN,
        pattern=re.compile(r'(?:ghu|ghs)_[A-Za-z0-9]{36}'),
        description="GitHub App installation/user token",
        confidence=0.98,
        env_var_names=("GITHUB_APP_TOKEN",),
    ),
    SecretPattern(
        name="GitHub Fine-grained PAT",
        secret_type=SecretType.GITHUB_PAT,
        pattern=re.compile(r'github_pat_[A-Za-z0-9_]{22,}'),
        description="GitHub fine-grained personal access token",
        confidence=0.98,
        env_var_names=("GITHUB_TOKEN", "GITHUB_PAT"),
    ),
    SecretPattern(
        name="GitLab Token",
        secret_type=SecretType.GITLAB_TOKEN,
        pattern=re.compile(r'glpat-[A-Za-z0-9_-]{20}'),
        description="GitLab personal access token",
        confidence=0.98,
        env_var_names=("GITLAB_TOKEN", "GITLAB_ACCESS_TOKEN"),
    ),
    SecretPattern(
        name="NPM Token",
        secret_type=SecretType.NPM_TOKEN,
        pattern=re.compile(r'npm_[A-Za-z0-9]{36}'),
        description="NPM access token",
        confidence=0.98,
        env_var_names=("NPM_TOKEN", "NPM_AUTH_TOKEN"),
    ),
    SecretPattern(
        name="PyPI Token",
        secret_type=SecretType.PYPI_TOKEN,
        pattern=re.compile(r'pypi-AgEIcHlwaS5vcmc[A-Za-z0-9_-]{50,}'),
        description="PyPI API token",
        confidence=0.98,
        env_var_names=("PYPI_TOKEN", "PYPI_API_TOKEN"),
    ),

    # -------------------------------------------------------------------------
    # Databases
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Database Connection URL",
        secret_type=SecretType.DATABASE_URL,
        pattern=re.compile(r'(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|mssql):\/\/[^\s"\'<>]+:[^\s"\'<>@]+@[^\s"\'<>]+'),
        description="Database connection string with credentials",
        confidence=0.95,
        env_var_names=("DATABASE_URL", "DB_URL", "CONNECTION_STRING"),
    ),
    SecretPattern(
        name="MongoDB URI",
        secret_type=SecretType.MONGODB_URI,
        pattern=re.compile(r'mongodb(?:\+srv)?:\/\/[^\s"\'<>]+:[^\s"\'<>@]+@[^\s"\'<>]+'),
        description="MongoDB connection string with credentials",
        confidence=0.95,
        env_var_names=("MONGODB_URI", "MONGO_URL"),
    ),
    SecretPattern(
        name="Supabase Key",
        secret_type=SecretType.SUPABASE_KEY,
        pattern=re.compile(r'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
        description="Supabase JWT key (anon or service role)",
        confidence=0.85,
        validator=validate_jwt,
        env_var_names=("SUPABASE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"),
    ),
    SecretPattern(
        name="Firebase Key",
        secret_type=SecretType.FIREBASE_KEY,
        pattern=re.compile(r'AIza[A-Za-z0-9_-]{35}'),
        description="Firebase API key",
        confidence=0.95,
        env_var_names=("FIREBASE_API_KEY",),
    ),

    # -------------------------------------------------------------------------
    # Payment/Finance
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Stripe Publishable Key",
        secret_type=SecretType.STRIPE_KEY,
        pattern=re.compile(r'pk_(?:live|test)_[A-Za-z0-9]{24,}'),
        description="Stripe publishable API key",
        confidence=0.98,
        env_var_names=("STRIPE_PUBLISHABLE_KEY", "STRIPE_PK"),
    ),
    SecretPattern(
        name="Stripe Secret Key",
        secret_type=SecretType.STRIPE_SECRET,
        pattern=re.compile(r'sk_(?:live|test)_[A-Za-z0-9]{24,}'),
        description="Stripe secret API key",
        confidence=0.98,
        env_var_names=("STRIPE_SECRET_KEY", "STRIPE_SK"),
    ),
    SecretPattern(
        name="Stripe Restricted Key",
        secret_type=SecretType.STRIPE_SECRET,
        pattern=re.compile(r'rk_(?:live|test)_[A-Za-z0-9]{24,}'),
        description="Stripe restricted API key",
        confidence=0.98,
        env_var_names=("STRIPE_RESTRICTED_KEY",),
    ),
    SecretPattern(
        name="Square Access Token",
        secret_type=SecretType.SQUARE_TOKEN,
        pattern=re.compile(r'sq0atp-[A-Za-z0-9_-]{22}'),
        description="Square access token",
        confidence=0.98,
        env_var_names=("SQUARE_ACCESS_TOKEN",),
    ),
    SecretPattern(
        name="Square OAuth Secret",
        secret_type=SecretType.SQUARE_TOKEN,
        pattern=re.compile(r'sq0csp-[A-Za-z0-9_-]{43}'),
        description="Square OAuth secret",
        confidence=0.98,
        env_var_names=("SQUARE_OAUTH_SECRET",),
    ),

    # -------------------------------------------------------------------------
    # Communication
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Twilio Account SID",
        secret_type=SecretType.TWILIO_SID,
        pattern=re.compile(r'AC[a-f0-9]{32}'),
        description="Twilio account SID",
        confidence=0.95,
        env_var_names=("TWILIO_ACCOUNT_SID",),
    ),
    SecretPattern(
        name="Twilio Auth Token",
        secret_type=SecretType.TWILIO_TOKEN,
        pattern=re.compile(r'(?i)(?:twilio_auth_token|twilio_token)["\s:=]+["\']?([a-f0-9]{32})["\']?'),
        description="Twilio auth token",
        confidence=0.85,
        env_var_names=("TWILIO_AUTH_TOKEN",),
    ),
    SecretPattern(
        name="SendGrid API Key",
        secret_type=SecretType.SENDGRID,
        pattern=re.compile(r'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}'),
        description="SendGrid API key",
        confidence=0.98,
        env_var_names=("SENDGRID_API_KEY",),
    ),
    SecretPattern(
        name="Mailgun API Key",
        secret_type=SecretType.MAILGUN,
        pattern=re.compile(r'key-[a-f0-9]{32}'),
        description="Mailgun API key",
        confidence=0.95,
        env_var_names=("MAILGUN_API_KEY",),
    ),
    SecretPattern(
        name="Slack Bot Token",
        secret_type=SecretType.SLACK_TOKEN,
        pattern=re.compile(r'xoxb-[0-9]{10,}-[0-9]{10,}-[A-Za-z0-9]{24}'),
        description="Slack bot token",
        confidence=0.98,
        env_var_names=("SLACK_BOT_TOKEN", "SLACK_TOKEN"),
    ),
    SecretPattern(
        name="Slack User Token",
        secret_type=SecretType.SLACK_TOKEN,
        pattern=re.compile(r'xoxp-[0-9]{10,}-[0-9]{10,}-[0-9]{10,}-[a-f0-9]{32}'),
        description="Slack user token",
        confidence=0.98,
        env_var_names=("SLACK_USER_TOKEN",),
    ),
    SecretPattern(
        name="Slack Webhook",
        secret_type=SecretType.SLACK_WEBHOOK,
        pattern=re.compile(r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+'),
        description="Slack incoming webhook URL",
        confidence=0.98,
        env_var_names=("SLACK_WEBHOOK_URL",),
    ),
    SecretPattern(
        name="Discord Bot Token",
        secret_type=SecretType.DISCORD_TOKEN,
        pattern=re.compile(r'[MN][A-Za-z0-9]{23,}\.[\w-]{6}\.[\w-]{27,}'),
        description="Discord bot token",
        confidence=0.90,
        env_var_names=("DISCORD_TOKEN", "DISCORD_BOT_TOKEN"),
    ),
    SecretPattern(
        name="Discord Webhook",
        secret_type=SecretType.DISCORD_WEBHOOK,
        pattern=re.compile(r'https://discord(?:app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+'),
        description="Discord webhook URL",
        confidence=0.98,
        env_var_names=("DISCORD_WEBHOOK_URL",),
    ),
    SecretPattern(
        name="Telegram Bot Token",
        secret_type=SecretType.TELEGRAM_TOKEN,
        pattern=re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}'),
        description="Telegram bot token",
        confidence=0.90,
        env_var_names=("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN"),
    ),

    # -------------------------------------------------------------------------
    # Storage/CDN
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Cloudflare API Key",
        secret_type=SecretType.CLOUDFLARE_KEY,
        pattern=re.compile(r'(?i)(?:cloudflare_api_key|cf_api_key)["\s:=]+["\']?([a-f0-9]{37})["\']?'),
        description="Cloudflare API key",
        confidence=0.85,
        env_var_names=("CLOUDFLARE_API_KEY", "CF_API_KEY"),
    ),
    SecretPattern(
        name="Cloudinary URL",
        secret_type=SecretType.CLOUDINARY_KEY,
        pattern=re.compile(r'cloudinary://[0-9]+:[A-Za-z0-9_-]+@[A-Za-z0-9_-]+'),
        description="Cloudinary connection URL",
        confidence=0.98,
        env_var_names=("CLOUDINARY_URL",),
    ),

    # -------------------------------------------------------------------------
    # Misc APIs
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Notion API Key",
        secret_type=SecretType.NOTION,
        pattern=re.compile(r'(?:ntn_|secret_)[A-Za-z0-9]{43,}'),
        description="Notion integration token",
        confidence=0.95,
        env_var_names=("NOTION_API_KEY", "NOTION_TOKEN"),
    ),
    SecretPattern(
        name="Airtable API Key",
        secret_type=SecretType.AIRTABLE,
        pattern=re.compile(r'key[A-Za-z0-9]{14}'),
        description="Airtable API key",
        confidence=0.85,
        env_var_names=("AIRTABLE_API_KEY",),
    ),
    SecretPattern(
        name="Brave Search API Key",
        secret_type=SecretType.BRAVE_SEARCH,
        pattern=re.compile(r'BSA[A-Za-z0-9_-]{40,}'),
        description="Brave Search API key",
        confidence=0.95,
        env_var_names=("BRAVE_API_KEY", "BRAVE_SEARCH_API_KEY"),
    ),

    # -------------------------------------------------------------------------
    # Cryptographic Keys
    # -------------------------------------------------------------------------
    SecretPattern(
        name="RSA Private Key",
        secret_type=SecretType.PRIVATE_KEY,
        pattern=re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
        description="Private key header",
        confidence=0.99,
        env_var_names=("PRIVATE_KEY",),
    ),
    SecretPattern(
        name="SSH Private Key",
        secret_type=SecretType.SSH_KEY,
        pattern=re.compile(r'-----BEGIN OPENSSH PRIVATE KEY-----'),
        description="OpenSSH private key",
        confidence=0.99,
        env_var_names=("SSH_PRIVATE_KEY",),
    ),
    SecretPattern(
        name="PGP Private Key",
        secret_type=SecretType.PRIVATE_KEY,
        pattern=re.compile(r'-----BEGIN PGP PRIVATE KEY BLOCK-----'),
        description="PGP private key block",
        confidence=0.99,
        env_var_names=("PGP_PRIVATE_KEY",),
    ),

    # -------------------------------------------------------------------------
    # Generic/Contextual Patterns (lower confidence, need context)
    # -------------------------------------------------------------------------
    SecretPattern(
        name="Generic API Key Assignment",
        secret_type=SecretType.API_KEY_GENERIC,
        pattern=re.compile(r'(?i)(?:api_?key|apikey|api_?secret|access_?key)["\s:=]+["\']?([A-Za-z0-9_-]{20,})["\']?'),
        description="Generic API key in code/config",
        confidence=0.60,
        env_var_names=("API_KEY",),
    ),
    SecretPattern(
        name="Generic Secret Assignment",
        secret_type=SecretType.SECRET,
        pattern=re.compile(r'(?i)(?:secret|secret_?key|client_?secret)["\s:=]+["\']?([A-Za-z0-9_-]{16,})["\']?'),
        description="Generic secret in code/config",
        confidence=0.55,
        env_var_names=("SECRET", "SECRET_KEY", "CLIENT_SECRET"),
    ),
    SecretPattern(
        name="Password Assignment",
        secret_type=SecretType.PASSWORD,
        pattern=re.compile(r'(?i)(?:password|passwd|pwd)["\s:=]+["\']?([^\s"\']{8,})["\']?'),
        description="Password in code/config",
        confidence=0.50,
        env_var_names=("PASSWORD", "DB_PASSWORD", "ADMIN_PASSWORD"),
    ),
    SecretPattern(
        name="JWT Token",
        secret_type=SecretType.JWT_SECRET,
        pattern=re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
        description="JWT token",
        confidence=0.80,
        validator=validate_jwt,
        env_var_names=("JWT_TOKEN", "AUTH_TOKEN"),
    ),
]


# Build lookup dictionaries for fast access
PATTERNS_BY_TYPE: dict[SecretType, list[SecretPattern]] = {}
for pattern in SECRET_PATTERNS:
    if pattern.secret_type not in PATTERNS_BY_TYPE:
        PATTERNS_BY_TYPE[pattern.secret_type] = []
    PATTERNS_BY_TYPE[pattern.secret_type].append(pattern)


def get_env_var_name(secret_type: SecretType) -> str:
    """Get the recommended environment variable name for a secret type."""
    patterns = PATTERNS_BY_TYPE.get(secret_type, [])
    if patterns and patterns[0].env_var_names:
        return patterns[0].env_var_names[0]
    return secret_type.value.upper()
