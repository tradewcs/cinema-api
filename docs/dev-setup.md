# Development Setup Guide

This guide will help you set up the Online Cinema project for local development using either Docker or a local Python environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Development Setup](#docker-development-setup)
- [Local Development Setup](#local-development-setup)
- [Database Migrations](#database-migrations)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### For Docker Setup
- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- Git

### For Local Setup
- Python 3.13 or later
- PostgreSQL 14 or later
- Redis 6 or later
- Poetry 1.5 or later
- Git

### Verify Installations

```bash
# Docker
docker --version
docker-compose --version

# Python
python --version

# Poetry
poetry --version

# PostgreSQL
psql --version

# Redis
redis-cli --version
```

## Docker Development Setup

Docker provides the easiest and most consistent development environment.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd online-cinema
```

### 2. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:


### 3. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
```

### 4. Run Database Migrations

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Create a new migration (if needed)
docker-compose exec app alembic revision --autogenerate -m "description"
```

### 5. Access the Application

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 7. Useful Docker Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild a specific service
docker-compose build app

# Restart a service
docker-compose restart app

# Execute a command in the app container
docker-compose exec app python -m pytest

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d online_cinema

# Access Redis CLI
docker-compose exec redis redis-cli

# View running containers
docker-compose ps

# Remove unused images and containers
docker system prune -a
```

## Local Development Setup

For development without Docker, follow these steps.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd online-cinema
```

### 2. Install Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Install Dependencies

```bash
# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 4. Set Up PostgreSQL

```bash
# Create database
createdb online_cinema

# Or using psql
psql -U postgres
CREATE DATABASE online_cinema;
\q
```

### 5. Set Up Redis

```bash
# Start Redis (macOS with Homebrew)
brew services start redis

# Or start manually
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 6. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Update database and Redis hosts for local development


### 7. Run Database Migrations

```bash
# Initialize Alembic (if needed)
alembic init src/alembic

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### 8. Set Up MinIO (Optional - for avatar storage)

```bash
# Install MinIO
brew install minio

# Start MinIO server
minio server ~/minio-data --console-address ":9001"

# Or use Docker for MinIO only
docker run -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

## Database Migrations

### Using Async Alembic

The project uses async Alembic for database migrations.

#### Configuration (`src/alembic/env.py`)

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.core.config import settings
from src.db.base import Base

# Import all models to ensure they're registered
from src.models import *

config = context.config
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode (async)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

#### Common Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "add users table"

# Apply all migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Show current revision
alembic current

# Show migration history
alembic history

# Show SQL for a migration without applying
alembic upgrade head --sql
```

## Running the Application

### Using Docker

```bash
# Start all services
docker-compose up

# Or in detached mode
docker-compose up -d
```

### Local Development

```bash
# Activate virtual environment
poetry shell

# Run FastAPI application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (in another terminal)
celery -A src.celery_app worker --loglevel=info

# Run Celery beat (in another terminal)
celery -A src.celery_app beat --loglevel=info
```

### Development Mode Features

- **Auto-reload**: Changes to code automatically restart the server
- **Debug mode**: Detailed error messages and stack traces
- **Interactive docs**: Available at `/docs` and `/redoc`

## Testing

### Using Docker

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/test_auth.py

# Run with markers
docker-compose exec app pytest -m unit
docker-compose exec app pytest -m integration
```

### Local Environment

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html
poetry run pytest --cov=src --cov-report=term-missing

# Run specific tests
poetry run pytest tests/test_auth.py::test_user_registration
poetry run pytest tests/test_auth.py -v

# Run with markers
poetry run pytest -m "unit"
poetry run pytest -m "integration"
poetry run pytest -m "not slow"

# Run tests in parallel
poetry run pytest -n auto
```

### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    auth: Authentication tests
    movies: Movie-related tests
    orders: Order-related tests
    payments: Payment-related tests
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
```

## Troubleshooting

### Docker Issues

**Problem**: Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Problem**: Database connection errors

```bash
# Check if PostgreSQL container is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Problem**: Migration errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec app alembic upgrade head
```

### Local Development Issues

**Problem**: Poetry dependencies conflict

```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

**Problem**: PostgreSQL connection refused

```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL (macOS)
brew services start postgresql@14

# Check connection
psql -U postgres -d online_cinema
```

**Problem**: Redis connection errors

```bash
# Check Redis is running
redis-cli ping

# Start Redis
redis-server

# Or with Homebrew
brew services start redis
```

**Problem**: Alembic migration conflicts

```bash
# Show current head
alembic current

# Show history
alembic history

# Stamp database to specific revision
alembic stamp head

# Merge multiple heads
alembic merge heads -m "merge migrations"
```

### Common Async Issues

**Problem**: `RuntimeError: Event loop is closed`

This usually happens when mixing sync and async code. Ensure:
- All database operations use `async with` and `await`
- Use `AsyncSession` instead of `Session`
- Use async versions of libraries (asyncpg, aioredis, etc.)

**Problem**: Database connections not closing

```python
# Always use context managers
async with get_db_session() as session:
    # Your database operations
    pass

# Or ensure proper cleanup
try:
    # operations
finally:
    await session.close()
```

## Getting Help

If you encounter issues:

1. Check this documentation
2. Search existing GitHub issues
3. Check application logs: `docker-compose logs -f`
4. Ask in the team chat
5. Create a new GitHub issue with:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs or error messages

---

**Happy Coding! 🚀**