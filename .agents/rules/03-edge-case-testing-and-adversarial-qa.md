# Rule 03: Adversarial Edge Case Testing & QA Standards

Testing is not complete simply because the happy-path unit test passes. Before approving code changes or opening a pull request, the test suite must address the following operational failure modes:

## 1. Adversarial Test Matrix Requirements
* **Idempotency & Replays**: Submit duplicate requests with identical idempotency keys concurrently and verify that only one record is created and identical responses are returned.
* **Network & Timeout Resilience**: Simulate third-party CRM webhook dropouts, partial 5xx responses, and exponential backoff retry behavior.
* **Concurrent Mutation Conflicts**: Test parallel write attempts to the same account or contact entity using multi-threaded test harnesses or transaction isolation tests.
* **Boundary Validation**: Null bytes, oversized payloads (>10MB), non-UTF8 strings, and extreme numeric values.

## 2. Testing Constraints
* **No Database Mocking in Integration Suites**: Integration tests must execute against real PostgreSQL/SQLite test instances with full foreign key constraints and triggers enabled.
* **Deterministic Fixtures**: Use `factory-boy` or deterministic pytest fixtures; never rely on hardcoded IDs or static dates that fail on new calendar days.
* **Rollback Cleanliness**: Tests must roll back state cleanly after each test case to prevent test pollution.
