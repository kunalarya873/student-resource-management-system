# Rule 01: CRM Backend Architecture & Codebase Standards

All code generated, refactored, or reviewed within this workspace must strictly adhere to the following architectural patterns:

## 1. Clean Architecture & Layer Separation
* **Models**: Define state and database constraints only. Do not place business orchestration logic directly inside Django model `save()` methods.
* **Services**: All state mutations (creating contacts, updating subscriptions, charging accounts, syncing external CRM APIs) must live in dedicated service functions (`<app>/services.py`).
* **Selectors**: Complex read queries, filtering, and aggregations must live in `<app>/selectors.py`.
* **Serializers / Schemas**: Strictly separate request validation schemas from response serialization schemas.

## 2. Transaction Integrity & Concurrency
* All multi-table write operations **MUST** be wrapped in `transaction.atomic()`.
* Use `select_for_update()` when modifying shared resources (e.g., account balance, seat allocation, subscription limits) to prevent race conditions.
* Always enforce idempotency keys on external webhook consumers and mutating API endpoints.

## 3. Query Performance & Zero N+1 Policy
* Every foreign key relationship accessed in serialization must use `select_related()`.
* Every many-to-many or reverse foreign key relationship accessed must use `prefetch_related()`.
* Unindexed lookups on high-cardinality fields (`email`, `external_crm_id`, `created_at`) are strictly prohibited.

## 4. Modern Python 3.12+ Standards
* Use explicit type annotations on all function signatures (`def sync_lead(lead_id: UUID, payload: LeadSyncDTO) -> SyncResult:`).
* Prefer `dataclasses` or `pydantic.BaseModel` for data transfer objects (DTOs).
