# Phase 9: Administration, Audit Logging & Storage Analytics

**Phase Number:** 09  
**Module:** System Administration, Immutable Audit Trails & Storage Oversight  
**Lead Agent:** **Domain Model Agent** (`Claude 3.7 Sonnet Thinking`)  
**Supporting Agents:** **Feature Executor Agent** (`Claude 3.5 Sonnet`), **Review Researcher Agent** (`Claude 3.7 Sonnet`), **Test Executor Agent** (`Claude 3.5 Sonnet`)  
**Governing Rules:** Rule 01 (Clean Layering & Selectors), Rule 02 (PII Minimization & Audit Trail)  
**Status:** Ready for Execution  

---

## 1. Phase Objective & Corex Handoff

Implement administrator governance tools, institutional storage utilization reporting, and an **immutable audit event logging pipeline** tracking sensitive lifecycle operations (PII access, permission grants, file deletions, quota modifications) in strict compliance with Rule 02 and GDPR standards.

### Handoff Contract
* **Input Context:** `AuditEvent` model from Phase 2, admin requirements from `phase10.md` (10.4.8 & 10.4.9), Rule 02 audit mandates.
* **Output Deliverable:** `app/services/audit_service.py`, `app/schemas/admin.py`, `app/api/v1/admin.py`, and `app/tests/test_admin.py`.
* **Acceptance Criteria:**
  1. All mutating operations emit an immutable `AuditEvent` with actor UUID, action type, entity ID, and masked details.
  2. Endpoints under `/api/v1/admin/*` are strictly protected with `require_role(["Administrator"])`.
  3. Storage reports calculate aggregated byte consumption grouped by department and user role.
  4. Administrators can adjust individual user storage quotas dynamically.

---

## 2. Audit Event Architecture & PII Masking

In compliance with Rule 02, sensitive identifiers logged in `details` are masked to prevent accidental PII exposure:

```python
def mask_email(email: str) -> str:
    """Masks email address for audit logging (e.g., k***a@domain.com)."""
    parts = email.split("@")
    if len(parts) != 2:
        return "***"
    name, domain = parts
    if len(name) <= 2:
        masked_name = name[0] + "***"
    else:
        masked_name = name[0] + "***" + name[-1]
    return f"{masked_name}@{domain}"
```

---

## 3. Step-by-Step Code Instructions

### Step 9.1: Audit Logging Service (`app/services/audit_service.py`)
```python
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditEvent
from app.models.user import User

class AuditService:
    @staticmethod
    async def log_event(
        session: AsyncSession,
        actor: User | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        details: dict[str, Any] | None = None,
    ):
        """Emits an immutable audit event to the database."""
        event = AuditEvent(
            actor_id=actor.user_id if actor else None,
            action=action.upper(),
            entity_type=entity_type.upper(),
            entity_id=entity_id,
            details=details or {},
        )
        session.add(event)
        # Flush event within current transaction boundary
        await session.flush()
```

### Step 9.2: Admin Schemas (`app/schemas/admin.py`)
```python
import uuid
from datetime import datetime
from pydantic import BaseModel

class UserQuotaUpdate(BaseModel):
    new_quota_bytes: int

class DepartmentStorageSummary(BaseModel):
    department_id: int | None
    department_name: str
    total_users: int
    total_quota_bytes: int
    total_used_bytes: int
    utilization_percentage: float

class SystemStorageReport(BaseModel):
    total_allocated_bytes: int
    total_used_bytes: int
    overall_utilization_percentage: float
    department_breakdown: list[DepartmentStorageSummary]

class AuditEventRead(BaseModel):
    event_id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_email: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    details: dict
    created_at: datetime
```

### Step 9.3: Administration API (`app/api/v1/admin.py`)
```python
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.dependencies import require_role
from app.models.audit import AuditEvent
from app.models.storage import StorageQuota
from app.models.user import Department, Role, User
from app.schemas.admin import AuditEventRead, SystemStorageReport, UserQuotaUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Administration"])

# Guard all routes in this router with Administrator role
AdminUser = Annotated[User, Depends(require_role(["Administrator"]))]

@router.get("/reports/storage", response_model=SystemStorageReport)
async def get_storage_report(
    admin: AdminUser, session: Annotated[AsyncSession, Depends(get_db_session)]
):
    # Total allocations
    total_quota = await session.scalar(select(func.coalesce(func.sum(StorageQuota.quota_bytes), 0)))
    total_used = await session.scalar(select(func.coalesce(func.sum(StorageQuota.used_bytes), 0)))

    pct = round((total_used / total_quota * 100), 2) if total_quota > 0 else 0.0

    return SystemStorageReport(
        total_allocated_bytes=total_quota,
        total_used_bytes=total_used,
        overall_utilization_percentage=pct,
        department_breakdown=[],
    )

@router.patch("/users/{user_id}/quota")
async def update_user_quota(
    user_id: uuid.UUID,
    payload: UserQuotaUpdate,
    admin: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    quota = await session.get(StorageQuota, user_id)
    if not quota:
        raise HTTPException(status_code=404, detail="User quota record not found")

    old_quota = quota.quota_bytes
    quota.quota_bytes = payload.new_quota_bytes

    await AuditService.log_event(
        session=session,
        actor=admin,
        action="UPDATE_USER_QUOTA",
        entity_type="STORAGE_QUOTA",
        entity_id=user_id,
        details={"old_quota": old_quota, "new_quota": payload.new_quota_bytes},
    )
    await session.commit()
    return {"message": "Quota updated successfully", "new_quota_bytes": quota.quota_bytes}

@router.get("/audit-logs", response_model=list[AuditEventRead])
async def list_audit_logs(
    admin: AdminUser,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditEvent.action == action.upper())
    events = (await session.scalars(stmt)).all()
    return events
```

---

## 4. Edge-Case & Adversarial Testing Matrix

| ID | Test Scenario | Trigger Condition | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **EC-09.1** | Teacher Access to Admin Routes | Authenticate as Teacher, call `GET /api/v1/admin/reports/storage` | Returns HTTP 403 Forbidden. |
| **EC-09.2** | Audit Immutability | Attempt to call `DELETE` or `PATCH` on `AuditEvent` table | Direct model has no update endpoints; database triggers reject modifications. |
| **EC-09.3** | Quota Reduction Below Used Bytes | Admin sets quota to 500 MB when user currently has 800 MB stored | Database check constraint `chk_quota_boundary` rejects change with HTTP 400. |

---

## 5. Verification Commands

```bash
# Run admin suite
pytest -v app/tests/test_admin.py

# Inspect storage report as admin
curl http://localhost:8000/api/v1/admin/reports/storage \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq .
```
