---
name: crm-edge-case-tester
description: Formulate and execute adversarial edge case test matrices for CRM APIs, webhook ingestion, and database concurrency.
---

# CRM Edge Case Tester Skill

Use this skill to systematically uncover and stress-test failure modes across CRM integration touchpoints.

## When to Use
* Testing new or modified webhook listeners (HubSpot, Salesforce, Stripe).
* Validating contact/account sync endpoints under race conditions.
* Designing stress tests for background queue workers.

## Procedure

### Step 1: Formulate Adversarial Matrix
Analyze target endpoint for the following dimensions:
1. **Network Chaos**: Timeout after 29s, sudden 502/504 Bad Gateway, payload truncation.
2. **Concurrency**: 20 simultaneous updates to the same contact email with conflicting phone numbers.
3. **Idempotency**: 5 identical requests fired in parallel with the exact same idempotency token.
4. **Data Fuzzing**: Unicode emojis, SQL injection attempts, null bytes, phone numbers in unusual international formats.

### Step 2: Implement Fixtures
Use pytest fixtures to construct clean, repeatable state:
```python
@pytest.fixture
def mock_crm_lead_payload():
    return {
        "email": "test.adversary+edge@example.com",
        "first_name": "Edge",
        "last_name": "Tester",
        "custom_attributes": {"limit_override": 99999999}
    }
```

### Step 3: Run Concurrency & Idempotency Verification
Execute multi-threaded test passes:
```bash
pytest -v -k "test_idempotent_lead_creation or test_concurrent_contact_mutation"
```

### Step 4: Validate Recovery & Rollback
Ensure no dirty records or orphan rows remain in SQLite/PostgreSQL after intentional failures.
