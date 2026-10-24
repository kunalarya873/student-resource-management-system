Viewed SKILL.md:1-42
Viewed implementation-playbook.md:1-150
Listed directory tests
Listed directory Student%20Resource%20Mangement%20System
Listed directory frontend
Listed directory phases_info
Viewed phase11.md:1-168
Viewed phase10.md:1-100
Viewed test_resources.py:1-80

### End-to-End (E2E) Testing Patterns Audit & Blueprint

This audit evaluates the system against the **`e2e-testing-patterns`** standard, reviewing our existing backend E2E API testing suite and establishing the architectural blueprint for full-stack browser-level E2E automation (Playwright).

---

### 1. The E2E Testing Pyramid & System Baseline

```
           /\
          /  \
         /E2E \         ← Critical User Journeys (Playwright & API journeys)
        /──────\
       / Integr \       ← Multi-Service Contracts (FastAPI + PostgreSQL + MinIO)
      /──────────\
     /    Unit    \     ← Logic, Schemas, Validators, Hashers
    /──────────────\
```

| Dimension | Current Backend State | E2E Browser Standard |
| :--- | :--- | :--- |
| **Test Count** | **49 test cases** | Full browser journey suites |
| **Execution Time** | **18.49 seconds** (~370ms avg per test) | Target: < 60s for smoke suite |
| **Database Isolation** | **Live PostgreSQL 16** (Zero mocking) | Dedicated isolated test seeds |
| **Object Storage** | **Live MinIO S3** (Presigned PUT/GET) | Real S3 endpoint integration |
| **Determinism** | **100% deterministic** (0 flaky tests) | Web-first assertions & auto-waiting |

---

### 2. E2E API Patterns Currently Implemented

The backend test suite already follows production-grade E2E integration patterns in [`app/tests/`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests):

#### A. Multi-Service End-to-End Asset Upload Pipeline
In [`test_resources.py` (`create_completed_upload`)](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_resources.py#L11-L48), tests do not mock S3 responses. Instead, the test runner executes the complete distributed journey:
1. `POST /api/v1/uploads/initiate` $\rightarrow$ FastAPI acquires row lock and issues MinIO presigned PUT URL.
2. Direct HTTP Client $\rightarrow$ Executes real `PUT` binary transfer directly to MinIO container.
3. `POST /api/v1/uploads/complete` $\rightarrow$ FastAPI performs `s3.head_object`, validates actual byte length and ETag, updates quota, and registers `StorageObject`.
4. `GET /api/v1/resources/{id}/download` $\rightarrow$ Verifies presigned GET URL and authorization headers.

#### B. Concurrency & Race Condition Verification
In [`test_quota_concurrency.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/test_quota_concurrency.py), 5 concurrent asynchronous coroutines fire simultaneous upload reservations against a 20 MiB quota balance. The test asserts that exactly the allowable quota is consumed and the 5th request is rejected with `413 Content Too Large` without deadlocks.

#### C. Clean Fixture Sharing
In [`app/tests/conftest.py`](file:///Users/kunalarya/Downloads/CRM_integration%20testing/antigravity-project/Student%20Resource%20Mangement%20System/backend/app/tests/conftest.py), token generation is centralized via `get_auth_token`, eliminating boilerplate across all 8 test modules.

---

### 3. Frontend & Full-Stack E2E Blueprint (Playwright)

For the presentation tier (`frontend/`), the system must employ **Playwright** with the following four core patterns:

#### Pattern 1: Page Object Model (POM) Structure
Decouple page selectors from test assertions. Every view has a dedicated class:

```typescript
// e2e/pages/ResourceUploadModal.ts
import { Page, Locator, expect } from '@playwright/test';

export class ResourceUploadModal {
    readonly page: Page;
    readonly fileInput: Locator;
    readonly titleInput: Locator;
    readonly descriptionInput: Locator;
    readonly submitButton: Locator;
    readonly progressBar: Locator;
    readonly successToast: Locator;

    constructor(page: Page) {
        this.page = page;
        this.fileInput = page.locator('input[data-testid="file-upload-input"]');
        this.titleInput = page.locator('input[data-testid="resource-title-input"]');
        this.descriptionInput = page.locator('textarea[data-testid="resource-desc-input"]');
        this.submitButton = page.locator('button[data-testid="submit-upload-btn"]');
        this.progressBar = page.locator('[data-testid="upload-progress-bar"]');
        this.successToast = page.locator('[data-testid="toast-success"]');
    }

    async uploadFile(filePath: string, title: string, description: string) {
        await this.fileInput.setInputFiles(filePath);
        await this.titleInput.fill(title);
        await this.descriptionInput.fill(description);
        await this.submitButton.click();
        await expect(this.progressBar).toBeHidden({ timeout: 15000 });
        await expect(this.successToast).toBeVisible();
    }
}
```

#### Pattern 2: Authentication State Caching (`storageState`)
Avoid logging in through the UI before every test. Playwright logs in once during global setup and saves JWT tokens to disk:

```typescript
// e2e/global-setup.ts
import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
    const browser = await chromium.launch();
    
    // 1. Authenticate Student
    const studentPage = await browser.newPage();
    await studentPage.goto('http://localhost:3000/login');
    await studentPage.fill('[data-testid="email-input"]', 'student@amu.edu');
    await studentPage.fill('[data-testid="password-input"]', 'StudentPass123!');
    await studentPage.click('[data-testid="login-submit-btn"]');
    await studentPage.waitForURL('**/dashboard');
    await studentPage.context().storageState({ path: 'e2e/.auth/student.json' });

    // 2. Authenticate Teacher
    const teacherPage = await browser.newPage();
    await teacherPage.goto('http://localhost:3000/login');
    await teacherPage.fill('[data-testid="email-input"]', 'teacher@amu.edu');
    await teacherPage.fill('[data-testid="password-input"]', 'TeacherPass123!');
    await teacherPage.click('[data-testid="login-submit-btn"]');
    await teacherPage.waitForURL('**/dashboard');
    await teacherPage.context().storageState({ path: 'e2e/.auth/teacher.json' });

    await browser.close();
}
export default globalSetup;
```

#### Pattern 3: Deterministic Web-First Assertions (Anti-Flake)
Never use arbitrary timeouts (`page.waitForTimeout(3000)`). Use Playwright's web-first auto-retrying assertions and network event matching:

```typescript
// e2e/tests/sharing.spec.ts
import { test, expect } from '@playwright/test';

test.use({ storageState: 'e2e/.auth/student.json' });

test('granting view permission displays resource in peer dashboard', async ({ page, browser }) => {
    // 1. Student shares private resource with Teacher
    await page.goto('/resources');
    await page.click('[data-testid="share-resource-btn-1"]');
    await page.fill('[data-testid="grantee-email-input"]', 'teacher@amu.edu');
    await page.selectOption('[data-testid="permission-select"]', 'VIEW');
    
    const [response] = await Promise.all([
        page.waitForResponse(res => res.url().includes('/api/v1/sharing') && res.status() === 201),
        page.click('[data-testid="confirm-share-btn"]'),
    ]);
    await expect(page.locator('[data-testid="grant-badge-teacher@amu.edu"]')).toBeVisible();

    // 2. Teacher verifies real-time visibility in separate context
    const teacherContext = await browser.newContext({ storageState: 'e2e/.auth/teacher.json' });
    const teacherPage = await teacherContext.newPage();
    await teacherPage.goto('/shared-with-me');
    await expect(teacherPage.locator('text=Student Private Study Notes')).toBeVisible();
    await teacherContext.close();
});
```

#### Pattern 4: Robust Selector Hierarchy
Enforce strict selector hygiene in frontend components:
1. `data-testid="entity-action"` (Primary — resilient to CSS/DOM refactorings).
2. Accessibility roles (`page.getByRole('button', { name: 'Upload' })`).
3. Label bindings (`page.getByLabel('Password')`).
4. **Avoid**: Raw CSS classes (`.btn-primary-v2 > div:nth-child(3)`), which break on design updates.

---

### 4. CI/CD Pipeline Configuration

```yaml
# .github/workflows/e2e.yml
name: End-to-End Test Suite

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Spin up Infrastructure
        run: docker compose -f docker-compose.prod.yml up -d --build
      - name: Run Backend Integration Suite
        run: docker compose exec -T backend pytest --durations=10
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      - name: Run Playwright E2E Suite
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

---

### 5. Summary & Actionable Recommendations

1. **Current Backend Suite**: 49/49 passing integration tests provide reliable API-level E2E coverage across all 10 system phases.
2. **Next Milestone**: When implementing the React frontend in `frontend/`, implement `data-testid` attributes on all form inputs, modals, and buttons from day one to enable automated Playwright test execution.