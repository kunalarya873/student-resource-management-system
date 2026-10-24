# Phase 4: Folder Management & Hierarchical Navigation

**Phase Number:** 04  
**Module:** Folder Tree Navigation & Cycle-Protected Hierarchies  
**Lead Agent:** **Codebase Design Agent** (`Claude 3.5 Sonnet`)  
**Supporting Agents:** **Feature Executor Agent** (`Claude 3.5 Sonnet`), **Edge Case Researcher Agent** (`Claude 3.7 Sonnet Thinking`), **Test Executor Agent** (`Claude 3.5 Sonnet`)  
**Governing Rules:** Rule 01 (Clean Layering & Selectors), Rule 02 (Object-Level Authorization)  
**Status:** Ready for Execution  

---

## 1. Phase Objective & Corex Handoff

Implement hierarchical folder organization with recursive tree traversal, DAG cycle prevention (preventing circular parenting such as `A -> B -> A`), strict ownership isolation, and deletion safeguards (`SD-09`: non-empty folders cannot be deleted).

### Handoff Contract
* **Input Context:** `Folder` entity from Phase 2, `SD-03` and `SD-09` requirements from `phase10.md`, process flows from `phase7.md`.
* **Output Deliverable:** `app/services/folder_service.py`, `app/schemas/folder.py`, `app/api/v1/folders.py`, and `app/tests/test_folder_dag.py`.
* **Acceptance Criteria:**
  1. Users can create root folders (`parent_folder_id = None`) and nested subfolders.
  2. Recursive CTE query resolves folder path breadcrumbs (`Root > Semester 1 > Notes`).
  3. Attempting to move a folder into itself or its own descendants is rejected with HTTP 400 Bad Request.
  4. Deleting a folder with child subfolders or resources is rejected with HTTP 409 Conflict.
  5. Users cannot view, modify, or delete another user's private folders.

---

## 2. API Contract Specification

| Method | Endpoint | Request Body | Response Body | Status Code |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/folders` | `FolderCreate` (`name`, `parent_folder_id`) | `FolderRead` | 201 Created |
| `GET` | `/api/v1/folders` | Query: `parent_id` (optional) | `list[FolderRead]` | 200 OK |
| `GET` | `/api/v1/folders/{id}/contents`| None | `FolderContentsResponse` (breadcrumbs, subfolders, resources) | 200 OK |
| `PATCH`| `/api/v1/folders/{id}` | `FolderUpdate` (`name`, `parent_folder_id`) | `FolderRead` | 200 OK |
| `DELETE`| `/api/v1/folders/{id}`| None | `{"message": "Folder deleted successfully"}` | 200 OK |

---

## 3. Step-by-Step Code Instructions

### Step 3.1: Folder Service with DAG Cycle Check (`app/services/folder_service.py`)
```python
import uuid
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.folder import Folder
from app.models.resource import Resource
from app.models.user import User

class FolderService:
    @staticmethod
    async def get_breadcrumbs(session: AsyncSession, folder_id: uuid.UUID) -> list[dict]:
        """Recursive CTE to build folder ancestor path from root to current folder."""
        query = text("""
            WITH RECURSIVE folder_path AS (
                SELECT folder_id, name, parent_folder_id, 1 as depth
                FROM folders
                WHERE folder_id = :folder_id
                UNION ALL
                SELECT f.folder_id, f.name, f.parent_folder_id, fp.depth + 1
                FROM folders f
                JOIN folder_path fp ON f.folder_id = fp.parent_folder_id
            )
            SELECT folder_id, name FROM folder_path ORDER BY depth DESC;
        """)
        result = await session.execute(query, {"folder_id": str(folder_id)})
        return [{"folder_id": str(row[0]), "name": row[1]} for row in result.fetchall()]

    @staticmethod
    async def is_descendant(
        session: AsyncSession, target_parent_id: uuid.UUID, folder_id: uuid.UUID
    ) -> bool:
        """Checks if target_parent_id is folder_id itself or any of its descendants (prevent cycles)."""
        if target_parent_id == folder_id:
            return True
        query = text("""
            WITH RECURSIVE descendants AS (
                SELECT folder_id, parent_folder_id
                FROM folders
                WHERE parent_folder_id = :folder_id
                UNION ALL
                SELECT f.folder_id, f.parent_folder_id
                FROM folders f
                JOIN descendants d ON f.parent_folder_id = d.folder_id
            )
            SELECT 1 FROM descendants WHERE folder_id = :target_parent_id;
        """)
        result = await session.execute(
            query, {"folder_id": str(folder_id), "target_parent_id": str(target_parent_id)}
        )
        return result.scalar() is not None

    @classmethod
    async def create_folder(
        cls, session: AsyncSession, user: User, name: str, parent_folder_id: uuid.UUID | None
    ) -> Folder:
        if parent_folder_id:
            parent = await session.get(Folder, parent_folder_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            if parent.owner_id != user.user_id and user.role.name != "Administrator":
                raise HTTPException(status_code=403, detail="Cannot create subfolder in another user's folder")

        folder = Folder(name=name.strip(), parent_folder_id=parent_folder_id, owner_id=user.user_id)
        session.add(folder)
        await session.commit()
        await session.refresh(folder)
        return folder

    @classmethod
    async def move_or_rename_folder(
        cls,
        session: AsyncSession,
        user: User,
        folder_id: uuid.UUID,
        new_name: str | None,
        new_parent_id: uuid.UUID | None,
    ) -> Folder:
        folder = await session.get(Folder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != user.user_id and user.role.name != "Administrator":
            raise HTTPException(status_code=403, detail="Permission denied")

        if new_parent_id is not None and new_parent_id != folder.parent_folder_id:
            # Check DAG cycle
            if await cls.is_descendant(session, new_parent_id, folder_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder into itself or one of its descendants (circular hierarchy).",
                )
            parent = await session.get(Folder, new_parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Target parent folder not found")
            folder.parent_folder_id = new_parent_id

        if new_name:
            folder.name = new_name.strip()

        await session.commit()
        await session.refresh(folder)
        return folder

    @classmethod
    async def delete_folder(cls, session: AsyncSession, user: User, folder_id: uuid.UUID):
        folder = await session.get(Folder, folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        if folder.owner_id != user.user_id and user.role.name != "Administrator":
            raise HTTPException(status_code=403, detail="Permission denied")

        # SD-09: Verify folder is empty
        child_folders = await session.scalar(
            select(func.count(Folder.folder_id)).where(Folder.parent_folder_id == folder_id)
        )
        child_resources = await session.scalar(
            select(func.count(Resource.resource_id)).where(Resource.folder_id == folder_id)
        )

        if (child_folders or 0) > 0 or (child_resources or 0) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder is not empty. Remove all subfolders and resources before deleting.",
            )

        await session.delete(folder)
        await session.commit()
```

---

## 4. Edge-Case & Adversarial Testing Matrix

| ID | Test Scenario | Trigger Condition | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **EC-04.1** | Self-Parenting Attempt | Call `PATCH /folders/{id}` with `parent_folder_id = {id}` | HTTP 400 Bad Request ("Cannot move folder into itself"). |
| **EC-04.2** | Deep Tree Cycle Attempt | Move grandparent folder A to become child of grandchild folder C | HTTP 400 Bad Request detected via recursive CTE. |
| **EC-04.3** | Non-Empty Deletion Rejection | Call `DELETE /folders/{id}` where folder contains 1 file | HTTP 409 Conflict with descriptive message (`SD-09`). |
| **EC-04.4** | Cross-Tenant Folder Access | Student B calls `GET /folders/{id}/contents` for Student A's private folder | HTTP 403 Forbidden. |

---

## 5. Verification Commands

```bash
# Run folder tests
pytest -v app/tests/test_folder_dag.py

# Create a root folder via API
curl -X POST http://localhost:8000/api/v1/folders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Computer Networks"}' | jq .
```
