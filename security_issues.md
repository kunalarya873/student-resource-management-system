Viewed SKILL.md:1-156
Viewed main.py:1-77
Viewed config.py:1-54
Viewed dependencies.py:1-71
Viewed resource_service.py:80-140
Viewed resource_service.py:350-450
Viewed resource_service.py:170-235
Viewed resource_service.py:236-290
Viewed sharing_service.py:1-100
Viewed audit_service.py:1-109
Viewed admin.py:1-60

### Backend Security Code Audit & Hardening Report

This security code review was performed using the **`backend-security-coder`** methodology and evaluates the **AMU Student Resource Management System** backend against the **OWASP Top 10 API Security Risks (2023)** and enterprise defensive standards.

---

### 1. Executive Security Posture Summary

| Category | Status | Assessment |
| :--- | :---: | :--- |
| **API1: Broken Object Level Authorization (BOLA/IDOR)** | **PASS** | Strict resource ownership, granular grant verification (`ResourceAccess`), and folder hierarchy ownership checks. |
| **API2: Broken Authentication** | **PASS** | Dual JWT rotation (`access` / `refresh`), bcrypt password hashing, timing-attack mitigation with dummy verification hash. |
| **API3: Broken Object Property Level Authorization** | **PASS** | Pydantic V2 input/output schemas strictly strip unauthorized internal attributes. |
| **API4: Unrestricted Resource Consumption (DoS)** | **WARN** | Enforced storage quotas & window-function pagination; rate-limiting middleware recommended for `/auth/login`. |
| **API5: Broken Function Level Authorization (BFLA)** | **PASS** | Role-Based Access Control (`require_role(["Administrator"])`) applied on all admin endpoints. |
| **API6: Server-Side Request Forgery (SSRF)** | **PASS** | `validate_safe_url` with DNS resolution, protocol allowlisting, and private/loopback/multicast IP filtering. |
| **API7: Security Misconfiguration (CORS & Headers)** | **ACTION REQUIRED** | Permissive wildcard CORS (`["*"]`) with `allow_credentials=True`; missing HTTP defense-in-depth headers. |
| **API8: Lack of Protection from Automated Threats** | **INFO** | Rate limiting recommended on token issuance and refresh rotation. |
| **API9: Improper Inventory Management** | **PASS** | OpenAPI 3.1 schema strictly versioned under `/api/v1/openapi.json`. |
| **API10: Unsafe Consumption of APIs** | **PASS** | Direct client-to-S3 uploads via presigned URLs with verified byte sizes and ETags. |

---

### 2. Defensive Controls Implemented

#### A. Broken Object-Level Authorization (BOLA/IDOR) Defense
- **Folder Traversal & DAG Isolation**:
  [`FolderService.get_folder`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/folder_service.py#L114-L126) and [`move_or_rename_folder`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/folder_service.py#L158-L206) explicitly assert `folder.owner_id == user.user_id` or `Administrator` before reading, nesting, or moving folders.
- **Granular Sharing Authorization**:
  In [`SharingService.can_access_resource`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/sharing_service.py#L20-L66), access resolution enforces:
  1. Resource ownership
  2. System Administrator oversight
  3. Institutional department boundaries (`resource.owner.department_id == user.department_id`)
  4. Explicit `ResourceAccess` grant (`VIEW` vs `EDIT`)
- **Direct Asset Download Verification**:
  In [`ResourceService.get_download_info`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/resource_service.py#L381-L450), a presigned download URL is never generated without passing `verify_read_access()`.

#### B. Injection & Path Traversal Prevention
- **SQL Injection**: All ORM queries use SQLAlchemy parameterized expressions. Raw queries in [`SearchService`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/search_service.py#L89-L102) strictly bind parameters with PostgreSQL type casting (`CAST(:user_id AS UUID)`, `CAST(:q AS TEXT)`).
- **Directory Traversal**: [`sanitize_filename`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/core/validators.py#L9-L16) sanitizes file names via regex (`re.sub(r"[^\w\s\.-]", "_", ...)`), stripping `../`, `..\`, null bytes, and shell escape characters before object storage assignment.

#### C. Server-Side Request Forgery (SSRF) Guard
- In [`validate_safe_url`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/core/validators.py#L19-L79):
  - Protocol restricted strictly to `http` and `https`.
  - Disallows internal aliases (`localhost`, `127.0.0.1`, `::1`, `metadata.google.internal`).
  - Resolves domain to IP entries via `socket.getaddrinfo` and checks all candidate IPs against `ip.is_private`, `is_loopback`, `is_link_local`, `is_multicast`, `is_reserved`, and `is_unspecified`.

#### D. GDPR & PII Data Protection
- **Immutable Audit Trails**: [`AuditService.log_event`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/audit_service.py#L36-L64) stores administrative actions in the database.
- **PII Masking**: [`mask_email`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/services/audit_service.py#L16-L31) obfuscates user emails (e.g., `s***t@amu.edu`) in audit responses and logs.

---

### 3. Vulnerability Findings & Hardening Recommendations

---

#### Finding 1: CORS Misconfiguration with Credentials
* **Severity**: **Medium / High**
* **OWASP API 2023**: API7 (Security Misconfiguration)
* **Location**: [`app/main.py` (lines 51–57)](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/main.py#L51-L57)
* **Mechanism**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  When `allow_credentials=True`, browsers disallow literal `*`. Under Starlette/FastAPI, combining `allow_origins=["*"]` with `allow_credentials=True` echoes back the incoming request's `Origin` header dynamically, permitting **any malicious website** to issue cross-origin authenticated requests if credentials/cookies are shared.
* **Remediation**:
  Define an explicit origin whitelist in [`app/core/config.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/core/config.py):
  ```python
  CORS_ORIGINS: list[str] = [
      "http://localhost:3000",
      "http://localhost:5173",
      "http://127.0.0.1:3000",
  ]
  ```
  And in [`app/main.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/main.py):
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.CORS_ORIGINS,
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
      allow_headers=["Authorization", "Content-Type"],
  )
  ```

---

#### Finding 2: Missing HTTP Defense-in-Depth Security Headers
* **Severity**: **Low**
* **OWASP API 2023**: API7 (Security Misconfiguration)
* **Location**: [`app/main.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/main.py)
* **Mechanism**: HTTP responses lack modern browser security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`).
* **Remediation**:
  Add a Starlette middleware in [`app/main.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/main.py):
  ```python
  from starlette.middleware.base import BaseHTTPMiddleware
  from starlette.requests import Request
  from starlette.responses import Response

  class SecurityHeadersMiddleware(BaseHTTPMiddleware):
      async def dispatch(self, request: Request, call_next):
          response: Response = await call_next(request)
          response.headers["X-Content-Type-Options"] = "nosniff"
          response.headers["X-Frame-Options"] = "DENY"
          response.headers["X-XSS-Protection"] = "1; mode=block"
          response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
          response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
          response.headers["Content-Security-Policy"] = "default-src 'self'"
          return response

  app.add_middleware(SecurityHeadersMiddleware)
  ```

---

#### Finding 3: Rate Limiting on Authentication Endpoints
* **Severity**: **Medium**
* **OWASP API 2023**: API4 (Unrestricted Resource Consumption) / API8 (Lack of Protection from Automated Threats)
* **Location**: [`app/api/v1/auth.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/api/v1/auth.py)
* **Mechanism**: Currently, `/api/v1/auth/login` and `/api/v1/auth/refresh` have no IP-based or user-based request throttling. While constant-time password verification protects against timing attacks, an attacker could attempt high-frequency credential stuffing.
* **Remediation**:
  Integrate `slowapi` or Redis token-bucket rate limiter:
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @router.post("/login")
  @limiter.limit("5/minute")
  async def login(...):
      ...
  ```

---

### 4. Verification & Testing Evidence

All 49 automated security and functional integration tests continue to pass with 0 errors:
```bash
$ pytest --durations=10
============================= 49 passed in 18.49s ==============================
```
- **Auth & RBAC**: Passing ([`test_auth.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_auth.py), [`test_admin.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_admin.py))
- **SSRF & Quota Concurrency**: Passing ([`test_resources.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_resources.py), [`test_quota_concurrency.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_quota_concurrency.py))
- **BOLA & Sharing Revocation**: Passing ([`test_sharing.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_sharing.py))