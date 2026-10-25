# Contributing to AMU Student Resource Management System

Thank you for your interest in contributing to the AMU Student Resource Management System!

---

## 🛠️ Development Workflow

1. **Fork & Branch:** Create a branch prefixed with feature type:
   - `feat/feature-name`
   - `fix/bug-fix`
   - `docs/doc-update`
   - `perf/optimization`

2. **Environment Setup:**
   ```bash
   make install
   ```

3. **Database Migrations:**
   When adding or modifying SQLAlchemy models:
   ```bash
   make db-migration-create msg="describe_change"
   make db-migrate
   ```

4. **Testing Requirements:**
   Every new feature or bugfix MUST include automated tests in `backend/app/tests/`.
   Verify the full suite passes with:
   ```bash
   make test
   ```

5. **Code Style & Formatting:**
   We enforce formatting with Ruff and strict TypeScript typing.
   Before committing, run:
   ```bash
   make lint
   make format
   ```

---

## 📜 Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add folder drag-and-drop batch move`
- `fix: prevent race condition in quota allocation`
- `docs: update API documentation for Supabase storage`
- `test: add edge cases for recursive DAG breadcrumb traversal`
