# Phase 1: Environment, Dependencies & Local Infrastructure

**Phase Number:** 01  
**Module:** System Foundation & Containerized Services  
**Lead Agent:** **Codebase Design Agent** (`Claude 3.5 Sonnet`)  
**Supporting Agents:** **Deployment Agent** (`GPT-4o`), **Test Executor Agent** (`Claude 3.5 Sonnet`)  
**Governing Rules:** Rule 01 (Clean Architecture & Modern Python 3.12+), Rule 02 (Zero Hardcoded Secrets)  
**Status:** Ready for Execution  

---

## 1. Phase Objective & Corex Handoff

Establish the core repository foundations, dependency management, asynchronous database connectivity, and containerized services for the **Student Resource Management System**.

### Handoff Contract
* **Input Context:** System scope from `phase10.md`, architectural patterns from Rule 01.
* **Output Deliverable:** Bootstrapped `backend/` directory, configured `docker-compose.yml`, healthy PostgreSQL 16 and MinIO object storage services, database connection pool, and working `/healthz` endpoint.
* **Acceptance Criteria:**
  1. `docker compose up -d` launches PostgreSQL and MinIO without errors.
  2. Database connection pool initializes asynchronously with health check passing.
  3. MinIO auto-creates the bucket `academic-resources`.
  4. `GET /healthz` returns `{"status": "ok", "db": "connected", "storage": "connected"}` with HTTP 200.

---

## 2. Directory Structure to Scaffold

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application factory
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic Settings
│   │   ├── database.py             # Async engine, sessionmaker, Base
│   │   ├── security.py             # Security utilities
│   │   ├── exceptions.py           # Domain exception handlers
│   │   └── dependencies.py         # Shared dependencies
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py           # V1 API router aggregator
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py                 # TimestampMixin, UUIDMixin
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── common.py               # Base Pydantic schemas, pagination
│   ├── repositories/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Pytest fixtures
│       ├── unit/
│       └── integration/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
docker-compose.yml
```

---

## 3. Step-by-Step Implementation Instructions

### Step 1.1: Configure `backend/pyproject.toml`
Create `backend/pyproject.toml` using modern Python 3.12+ standards:

```toml
[project]
name = "student-resource-management-backend"
version = "0.1.0"
description = "Cloud-Based Academic Resource Management System Backend"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt>=4.1.2",
    "boto3>=1.34.0",
    "aioboto3>=13.0.0",
    "python-multipart>=0.0.9",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["app/tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"
```

### Step 1.2: Environment Configuration (`app/core/config.py`)
Implement type-safe configuration via `pydantic-settings`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "AMU Student Resource Management System"
    APP_ENV: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "amu_user"
    POSTGRES_PASSWORD: str = "amu_password_secure"
    POSTGRES_DB: str = "amu_resources_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @property
    def ASYNC_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # S3 / MinIO Object Storage
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "academic-resources"
    S3_REGION: str = "us-east-1"

    # JWT Authentication
    JWT_SECRET_KEY: str = "SUPER_SECRET_CHANGE_IN_PRODUCTION_KEY_32_BYTES_MIN"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage Quota Policies (in bytes)
    STUDENT_DEFAULT_QUOTA_BYTES: int = 1_073_741_824   # 1 GiB
    TEACHER_DEFAULT_QUOTA_BYTES: int = 16_106_127_360  # 15 GiB
    UPLOAD_RESERVATION_TIMEOUT_MINUTES: int = 30

settings = Settings()
```

### Step 1.3: Asynchronous Database Engine (`app/core/database.py`)
```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Step 1.4: Multi-Service `docker-compose.yml`
Create root `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: amu_postgres
    environment:
      POSTGRES_USER: amu_user
      POSTGRES_PASSWORD: amu_password_secure
      POSTGRES_DB: amu_resources_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amu_user -d amu_resources_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:RELEASE.2024-05-10T01-41-38Z
    container_name: amu_minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio-init:
    image: minio/mc:RELEASE.2024-05-09T17-04-24Z
    container_name: amu_minio_init
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set local http://minio:9000 minioadmin minioadmin;
      /usr/bin/mc mb --ignore-existing local/academic-resources;
      /usr/bin/mc anonymous set download local/academic-resources;
      exit 0;
      "

volumes:
  postgres_data:
  minio_data:
```

### Step 1.5: Application Lifespan & Health Check (`app/main.py`)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connectivity on startup
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    # Clean up engine pool on shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    async with engine.connect() as conn:
        db_res = await conn.execute(text("SELECT 1"))
        db_healthy = db_res.scalar() == 1
    return {
        "status": "ok",
        "database": "connected" if db_healthy else "error",
        "environment": settings.APP_ENV,
    }
```

---

## 4. Edge-Case & Adversarial Testing Matrix

| ID | Test Scenario | Trigger Condition | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **EC-01.1** | PostgreSQL container unreachable | Stop postgres container, call `/healthz` | Endpoint returns 500 or reports database "error" cleanly without crashing process. |
| **EC-01.2** | MinIO bucket already exists | Restart `minio-init` container | Initialization runs idempotently with `--ignore-existing`. |
| **EC-01.3** | DB Pool Exhaustion | Concurrently fire 50 connection requests beyond `DATABASE_MAX_OVERFLOW` | Requests wait gracefully or raise clean timeout without corrupting pool state. |

---

## 5. Verification Commands

```bash
# 1. Start Docker containers
docker compose up -d

# 2. Check container status
docker compose ps

# 3. Install backend dependencies
cd backend && pip install -e ".[dev]"

# 4. Run healthcheck verification
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl -s http://localhost:8000/healthz | jq .
```
