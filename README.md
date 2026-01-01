# IndexerAPI

**Enterprise File Indexing Service** - Fast, scalable file indexing as a REST API.

## Features

- **High-Performance Indexing**: Multi-threaded file system scanning
- **REST API**: Full CRUD operations for indexes and files
- **Search & Queries**: Filter by name, extension, size, date
- **Duplicate Detection**: Find duplicate files by content hash
- **Multi-Tenant**: Organizations with user management
- **API Keys**: Programmatic access with scoped permissions
- **Background Jobs**: Async indexing with Celery
- **Docker Ready**: Production-ready containerization

## Quick Start

### Option 1: Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Initialize database
indexer-api init-db

# Start the server
indexer-api serve --reload
```

### Option 2: Docker

```bash
# Development mode
docker-compose -f docker-compose.dev.yml up

# Production mode
docker-compose up -d
```

## API Usage

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "organization_name": "My Company"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=SecurePass123!"

# Use the access_token in subsequent requests
export TOKEN="your-access-token"
```

### Create an Index

```bash
curl -X POST http://localhost:8000/api/v1/indexes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Projects",
    "root_path": "C:\\Users\\me\\Projects",
    "include_patterns": ["*.py", "*.js", "*.ts"],
    "exclude_patterns": ["*node_modules*", "*.git*"]
  }'
```

### Start Indexing

```bash
curl -X POST http://localhost:8000/api/v1/indexes/{index_id}/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"job_type": "full_scan"}'
```

### Search Files

```bash
curl "http://localhost:8000/api/v1/indexes/{index_id}/files?query=main&extension=.py" \
  -H "Authorization: Bearer $TOKEN"
```

### Find Duplicates

```bash
curl http://localhost:8000/api/v1/indexes/{index_id}/duplicates \
  -H "Authorization: Bearer $TOKEN"
```

## CLI Commands

```bash
# Start API server
indexer-api serve --host 0.0.0.0 --port 8000

# Start Celery worker
indexer-api worker --concurrency 4

# Initialize database
indexer-api init-db

# Create a user
indexer-api create-user --email user@example.com --password Pass123! --org "My Org"

# Create an API key
indexer-api create-api-key --email user@example.com --name "CI/CD" --scopes "read,write"

# Show configuration
indexer-api info

# List routes
indexer-api routes
```

## Configuration

Configuration via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | development | development/staging/production |
| `DEBUG` | false | Enable debug mode |
| `DATABASE_URL` | sqlite+aiosqlite:///./indexer.db | Database connection |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `SECRET_KEY` | (required) | JWT secret key |
| `API_PREFIX` | /api/v1 | API route prefix |

See `src/indexer_api/core/config.py` for all options.

## Project Structure

```
indexer-api/
├── src/indexer_api/
│   ├── api/
│   │   ├── deps.py          # Dependencies (auth, db)
│   │   └── routers/         # API endpoints
│   │       ├── auth.py      # Authentication
│   │       ├── indexes.py   # Index management
│   │       └── health.py    # Health checks
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── security.py      # JWT, passwords
│   │   └── logging.py       # Structured logging
│   ├── db/
│   │   ├── base.py          # Database setup
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Auth service
│   │   └── indexer.py       # Indexing service
│   ├── workers/             # Celery tasks
│   ├── cli.py               # CLI commands
│   └── main.py              # FastAPI app
├── tests/
├── docker/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/indexer_api

# Lint
ruff check src tests

# Type check
mypy src
```

## License

MIT License
