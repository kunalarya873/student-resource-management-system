# AMU Student Resource Management System 🎓📂

[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20Storage-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Tests](https://img.shields.io/badge/Tests-88%20Passed-brightgreen.svg?style=flat)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A cloud-native academic resource repository and file management platform designed for educational institutions. Provides seamless Google Drive-style file hierarchies, role-based resource access control, asynchronous upload reservations, time-bounded signed URLs, and real-time quota governance powered by **FastAPI**, **PostgreSQL / Supabase**, and **React 19**.

---

## 🏗️ System Architecture

```
                                  ┌─────────────────────────────┐
                                  │      React 19 + Vite UI     │
                                  │   (Google Drive Interface)  │
                                  └──────────────┬──────────────┘
                                                 │
                                                 │ HTTPS / JSON & Multipart
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │       FastAPI Gateway       │
                                  │ (JWT Auth, RBAC, Quota, DAG)│
                                  └──────┬───────────────┬──────┘
                                         │               │
                     SQLAlchemy 2.0 Async│               │ Supabase Storage Client
                                         ▼               ▼
                 ┌─────────────────────────────┐   ┌─────────────────────────────┐
                 │     Supabase PostgreSQL     │   │      Supabase Storage       │
                 │   - 19 Relational Tables    │   │  - User-isolated directories│
                 │   - Recursive CTEs for DAG  │   │  - Time-bounded signed URLs │
                 │   - Quota Check Constraints │   │  - Asynchronous webhooks    │
                 └─────────────────────────────┘   └─────────────────────────────┘
```

---

## ✨ Core Features

- **Google Drive-Style File & Folder Management:**
  - True recursive Folder DAG with cycle prevention, breadcrumbs via SQL Recursive CTEs, and cascading deletions.
  - Multi-tier search: Full-Text Search (FTS) across title, description, tags, and subject metadata.
- **Dual Upload Pathways:**
  - **Direct Upload:** Fast multipart upload stream routed directly to user-isolated folders in Supabase Storage.
  - **Chunked / Presigned Direct S3 Upload:** Two-phase upload reservation workflow (`POST /api/v1/uploads/initiate` $\rightarrow$ direct client PUT to storage $\rightarrow$ completion verification or Supabase storage webhook).
- **Strict Role-Based Access Control (RBAC):**
  - Roles: `Administrator`, `Teacher`, `Student`.
  - Privacy rules: Student resources remain private by default; Teacher uploads can be automatically approved and published institution-wide.
  - Granular Resource Sharing: Share resources with specific peers (`VIEWER` or `EDITOR` permissions) with real-time email dispatch.
- **Enterprise Storage Quota Governance:**
  - Automated quota tracking with atomic database row locks (`SELECT FOR UPDATE`) to prevent race conditions during concurrent uploads.
  - Automatic expiration and rollback of abandoned upload reservations.
- **Modern Authentication & Account Security:**
  - Dual verification: Cryptographic 6-digit numeric OTPs and time-bounded JWT email verification tokens.
  - Password reset with rate-limiting, timing-attack countermeasures, and anti-enumeration safeguards.

---

## 🛠️ Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous, auto-generating OpenAPI 3.1, high throughput with Uvicorn. |
| **Database & ORM** | [PostgreSQL](https://postgresql.org) via [Supabase](https://supabase.com) + [SQLAlchemy 2.0 Async](https://sqlalchemy.org) | End-to-end asyncpg driver, connection pooling, recursive CTE DAG operations. |
| **Storage Engine** | [Supabase Storage](https://supabase.com/storage) | S3-compatible, user folder segregation, presigned URLs, and event webhooks. |
| **Schema Migrations** | [Alembic](https://alembic.sqlalchemy.org/) | Deterministic schema versioning with zero-downtime safety checks. |
| **Frontend Framework** | [React 19](https://react.dev) + [Vite](https://vitejs.dev) | Modern ESM tooling, TanStack React Query v5, Tailwind CSS, Lucide icons. |
| **Code Quality** | [Ruff](https://astral.sh/ruff) + [uv](https://astral.sh/uv) | Blazing-fast Python packaging, strict linting, and formatting. |

---

## 🚀 Quickstart Guide

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Node.js](https://nodejs.org/) v18+ and `npm`
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-org/student-resource-management-system.git
cd "Student Resource Mangement System"

# Install all backend and frontend dependencies
make install
```

### 2. Configure Environment Variables

Create your backend configuration by copying the example:

```bash
cp backend/.env.example backend/.env
```

Ensure your `backend/.env` contains the database and Supabase credentials:
```env
# Database
DATABASE_URL="postgresql+asyncpg://postgres.ijlfghksvuyoynshxoif:YOUR_PASSWORD@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?ssl=require"

# Supabase Storage
SUPABASE_URL="https://ijlfghksvuyoynshxoif.supabase.co"
SUPABASE_KEY="your-supabase-anon-key"
SUPABASE_SERVICE_ROLE="your-supabase-service-role-key"
SUPABASE_BUCKET="resources"
SUPABASE_REGION="ap-southeast-2"
```

### 3. Apply Migrations & Seed Database

```bash
# Apply all 6 database schema migrations
make db-migrate

# Seed roles, departments, subjects, and test user accounts
make db-seed
```

### 4. Run Development Servers

```bash
# In terminal 1 (FastAPI backend on port 8000):
make dev-backend

# In terminal 2 (React frontend on port 5173):
make dev-frontend
```

Open your browser to:
- **Frontend Application:** [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing & Code Quality

The backend includes a comprehensive automated test suite covering unit tests, DAG recursive hierarchy verification, adversarial concurrency attacks, and Supabase storage lifecycle checks:

```bash
# Run all tests (88 test cases)
make test

# Run tests with coverage report
make test-cov

# Lint and check code formatting
make lint
make format
```

---

## 📦 Make Automation Reference

| Command | Action |
| :--- | :--- |
| `make help` | Show all available Makefile commands |
| `make install` | Install both backend and frontend dependencies |
| `make dev-backend` | Start FastAPI with live reload on `:8000` |
| `make dev-frontend`| Start Vite React dev server on `:5173` |
| `make db-migrate` | Apply Alembic migrations to database |
| `make db-seed` | Seed default test data |
| `make test` | Run pytest suite |
| `make format` | Auto-format backend with Ruff |
| `make docker-up` | Launch production stack with Docker Compose |
| `make clean` | Clean up build artifacts, cache, and coverage files |

---

## 🔒 Security & Data Governance

- **GDPR & Privacy by Design:** Data subject segregation, Right-to-be-Forgotten deletion cascades, and isolated storage namespaces per user.
- **SSRF & Attack Prevention:** Strict URL validation preventing loopback/metadata exploits on external links.
- **Cryptographic Storage:** Secrets and passwords hashed with Bcrypt (12 rounds) and constant-time dummy verification against timing attacks.

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).
