# Phase 8: Search, Discovery & Metadata Filtering

**Phase Number:** 08  
**Module:** High-Performance Full-Text Search & Faceted Discovery Engine  
**Lead Agent:** **Codebase Design Agent** (`Claude 3.5 Sonnet`)  
**Supporting Agents:** **Feature Executor Agent** (`Claude 3.5 Sonnet`), **Test Executor Agent** (`Claude 3.5 Sonnet`), **Review Researcher Agent** (`Claude 3.7 Sonnet`)  
**Governing Rules:** Rule 01 (Query Performance & Zero N+1 Policy), Rule 02 (Data Minimization & Authorization)  
**Status:** Ready for Execution  

---

## 1. Phase Objective & Corex Handoff

Implement PostgreSQL-native Full-Text Search (FTS) using GIN indexes and faceted query filtering while enforcing a **zero-leakage security predicate** ensuring private resources are never exposed in search results.

### Handoff Contract
* **Input Context:** Requirements `SD-02` from `phase10.md`, `Resource` model and sharing relations from Phase 2 & 7.
* **Output Deliverable:** Alembic migration adding FTS GIN index, `app/services/search_service.py`, `app/api/v1/search.py`, and `app/tests/test_search.py`.
* **Acceptance Criteria:**
  1. Searches against `title` and `description` utilize PostgreSQL `plainto_tsquery` and GIN index.
  2. Search filters support `subject_id`, `department_id`, `academic_year_id`, and pagination (`page`, `limit`).
  3. **Strict Privacy Isolation:** Under no circumstances does a search query return another student's private unshared resource.
  4. Response time is < 50ms for indexed metadata queries.

---

## 2. Security Predicate Architecture

All search queries are injected with a mandatory SQL security clause before execution:

```sql
WHERE (
    -- 1. Caller owns the resource
    resources.owner_id = :current_user_id
    -- 2. Caller has Administrator privilege
    OR :is_admin = TRUE
    -- 3. Resource is approved institutional content
    OR (
        resources.status = 'APPROVED' 
        AND (resources.visibility = 'PUBLIC' OR resources.subject_id IN (SELECT subject_id FROM student_subject WHERE student_id = :current_user_id))
    )
    -- 4. Resource was explicitly shared with caller
    OR resources.resource_id IN (
        SELECT resource_id FROM resource_access WHERE user_id = :current_user_id
    )
)
```

---

## 3. Step-by-Step Code Instructions

### Step 8.1: Full-Text Search Migration (`alembic`)
Add a migration to create a PostgreSQL GIN index on `resources`:

```python
# In alembic version:
def upgrade():
    op.execute("""
        CREATE INDEX idx_resources_fts ON resources 
        USING gin(to_tsvector('english', title || ' ' || coalesce(description, '')));
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_resources_fts;")
```

### Step 8.2: Search Schemas (`app/schemas/search.py`)
```python
import uuid
from pydantic import BaseModel

class SearchResultItem(BaseModel):
    resource_id: uuid.UUID
    title: str
    description: str | None
    subject_code: str | None
    subject_name: str | None
    owner_name: str
    visibility: str
    rank: float

class SearchResponse(BaseModel):
    total_count: int
    page: int
    limit: int
    results: list[SearchResultItem]
```

### Step 8.3: Search Service Implementation (`app/services/search_service.py`)
```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.search import SearchResponse, SearchResultItem

class SearchService:
    @classmethod
    async def search_resources(
        cls,
        session: AsyncSession,
        user: User,
        query: str | None,
        subject_id: int | None,
        department_id: int | None,
        page: int = 1,
        limit: int = 20,
    ) -> SearchResponse:
        offset = (page - 1) * limit
        is_admin = user.role.name == "Administrator"

        sql = """
            SELECT 
                r.resource_id,
                r.title,
                r.description,
                s.code as subject_code,
                s.name as subject_name,
                u.full_name as owner_name,
                r.visibility,
                ts_rank(to_tsvector('english', r.title || ' ' || coalesce(r.description, '')), plainto_tsquery('english', :q)) as rank,
                count(*) OVER() AS total_count
            FROM resources r
            LEFT JOIN subjects s ON r.subject_id = s.subject_id
            JOIN users u ON r.owner_id = u.user_id
            WHERE 
                (
                    :q IS NULL OR 
                    to_tsvector('english', r.title || ' ' || coalesce(r.description, '')) @@ plainto_tsquery('english', :q)
                )
                AND (:subject_id IS NULL OR r.subject_id = :subject_id)
                AND (:department_id IS NULL OR s.department_id = :department_id)
                -- Mandatory Security Predicate
                AND (
                    r.owner_id = :user_id
                    OR :is_admin = TRUE
                    OR (r.status = 'APPROVED' AND (r.visibility = 'PUBLIC' OR s.department_id = :user_dept_id))
                    OR r.resource_id IN (SELECT resource_id FROM resource_access WHERE user_id = :user_id)
                )
            ORDER BY rank DESC, r.created_at DESC
            LIMIT :limit OFFSET :offset;
        """

        params = {
            "q": query.strip() if query else None,
            "subject_id": subject_id,
            "department_id": department_id,
            "user_id": str(user.user_id),
            "user_dept_id": user.department_id,
            "is_admin": is_admin,
            "limit": limit,
            "offset": offset,
        }

        result = await session.execute(text(sql), params)
        rows = result.fetchall()

        items = []
        total = 0
        for r in rows:
            total = r[8]
            items.append(
                SearchResultItem(
                    resource_id=r[0],
                    title=r[1],
                    description=r[2],
                    subject_code=r[3],
                    subject_name=r[4],
                    owner_name=r[5],
                    visibility=r[6],
                    rank=float(r[7] or 0.0),
                )
            )

        return SearchResponse(total_count=total, page=page, limit=limit, results=items)
```

---

## 4. Edge-Case & Adversarial Testing Matrix

| ID | Test Scenario | Trigger Condition | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **EC-08.1** | Private Data Leak via Search | Student B searches exact title of Student A's private, unshared assignment | 0 results returned. Private data never leaks. |
| **EC-08.2** | SQL Injection via Search Term | Query input contains `'; DROP TABLE resources; --` | Parameterized execution cleanly neutralizes injection without error. |
| **EC-08.3** | Special Characters & Punctuation | Search query contains `&& || ! ( ) < > : *` | `plainto_tsquery` sanitizes special FTS characters safely. |
| **EC-08.4** | Empty Search Query with Filters | Query parameter `q` is omitted, but `subject_id=1` is provided | Returns all permitted resources under subject 1 sorted by creation date. |

---

## 5. Verification Commands

```bash
# Run search test suite
pytest -v app/tests/test_search.py

# Search resources via API
curl "http://localhost:8000/api/v1/search?q=Algorithms&page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq .
```
