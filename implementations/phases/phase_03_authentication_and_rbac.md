# Phase 3: Authentication, Authorization & User Management

**Phase Number:** 03  
**Module:** Authentication & Role-Based Access Control (RBAC)  
**Lead Agent:** **Feature Executor Agent** (`Claude 3.5 Sonnet`)  
**Supporting Agents:** **Feature Researcher Agent** (`Gemini 2.0 Pro`), **Edge Case Researcher Agent** (`Claude 3.7 Sonnet Thinking`), **Review Researcher Agent** (`Claude 3.7 Sonnet`)  
**Governing Rules:** Rule 01 (Clean Layering & Modern Python), Rule 02 (Zero Hardcoded Secrets, RBAC Enforcement)  
**Status:** Ready for Execution  

---

## 1. Phase Objective & Corex Handoff

Deliver production-grade authentication with password hashing (bcrypt), dual-token JWT architecture (access and refresh tokens), user context resolution, and declarative role-based authorization dependencies (`require_role`).

### Handoff Contract
* **Input Context:** User and Role entities from Phase 2, security standards from Rule 02, endpoint contracts from `phase10.md` (10.4.1 & 10.6).
* **Output Deliverable:** `app/core/security.py`, `app/core/dependencies.py`, `app/schemas/auth.py`, `app/services/auth_service.py`, and `app/api/v1/auth.py`.
* **Acceptance Criteria:**
  1. `POST /api/v1/auth/login` verifies bcrypt hash and issues access + refresh tokens.
  2. Access tokens expire in 60 minutes; refresh tokens can issue new access tokens.
  3. `GET /api/v1/auth/me` returns current user, role, department, and quota summary.
  4. Role guard dependency raises HTTP 403 Forbidden when a student attempts to access teacher/admin protected endpoints.

---

## 2. API Contract Specification

| Method | Endpoint | Request Body | Response Body | Auth Required |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | `LoginRequest` (`email`, `password`) | `TokenResponse` (`access_token`, `refresh_token`, `token_type`) | None |
| `POST` | `/api/v1/auth/refresh`| `RefreshTokenRequest` (`refresh_token`) | `TokenResponse` (`access_token`, `refresh_token`) | None |
| `POST` | `/api/v1/auth/logout` | None | `{"message": "Logged out successfully"}` | Yes |
| `GET` | `/api/v1/auth/me` | None | `UserProfileResponse` | Yes |
| `GET` | `/api/v1/users/me` | None | `UserDetailsResponse` | Yes |
| `PATCH`| `/api/v1/users/me` | `UserUpdateRequest` (`full_name`) | `UserDetailsResponse` | Yes |

---

## 3. Step-by-Step Code Instructions

### Step 3.1: Security Utility Module (`app/core/security.py`)
```python
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str | Any, role: str, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "role": role, "type": "access", "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(subject), "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
```

### Step 3.2: Declarative RBAC Dependencies (`app/core/dependencies.py`)
```python
import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db_session
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise credentials_exception

    stmt = select(User).options(selectinload(User.role), selectinload(User.department)).where(User.user_id == user_id)
    user = await session.scalar(stmt)
    if user is None:
        raise credentials_exception
    if user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
    return user

def require_role(allowed_roles: list[str]):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker
```

### Step 3.3: Authentication Schemas (`app/schemas/auth.py`)
```python
import uuid
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfileResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role_name: str
    department_name: str | None = None
    status: str
```

### Step 3.4: Router Endpoints (`app/api/v1/auth.py`)
Wire endpoints with validation, exception handling, and audit event emission.

---

## 4. Edge-Case & Adversarial Testing Matrix

| ID | Test Scenario | Trigger Condition | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **EC-03.1** | Refresh Token Used as Access Token | Send refresh token in `Authorization: Bearer <token>` to protected route | Rejected with HTTP 401 ("Could not validate credentials"). |
| **EC-03.2** | Expired Access Token | Make request with token past `ACCESS_TOKEN_EXPIRE_MINUTES` | Rejected with HTTP 401. |
| **EC-03.3** | Role Escalation Attempt | Authenticate as Student, call endpoint protected with `require_role(["Teacher"])` | Rejected with HTTP 403 Forbidden. |
| **EC-03.4** | Inactive User Token | User marked "SUSPENDED" in database attempts API call with valid JWT | Rejected with HTTP 403 ("Inactive user account"). |
| **EC-03.5** | Timing Attack Resistance | Measure response time of non-existent user vs. invalid password | `pwd_context.verify()` called against dummy hash to maintain constant-time response. |

---

## 5. Verification Commands

```bash
# 1. Run unit and integration tests for auth
pytest -v app/tests/test_auth.py

# 2. Test login endpoint via curl
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "student@amu.edu", "password": "amu_demo_2026!"}' | jq .

# 3. Test /auth/me with Bearer token
TOKEN="<paste_access_token_here>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/me | jq .
```
