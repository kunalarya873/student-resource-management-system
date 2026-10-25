.DEFAULT_GOAL := help

# Variables
PYTHON ?= uv run python
UV ?= uv
NPM ?= npm
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: help
help: ## Display this help message
	@echo "Available commands for Student Resource Management System:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# -----------------------------------------------------------------------------
# Setup & Installation
# -----------------------------------------------------------------------------
.PHONY: install
install: install-backend install-frontend ## Install dependencies for both backend and frontend

.PHONY: install-backend
install-backend: ## Install Python backend dependencies using uv
	@echo "==> Installing backend dependencies with uv..."
	cd $(BACKEND_DIR) && $(UV) sync

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies with npm
	@echo "==> Installing frontend dependencies with npm..."
	cd $(FRONTEND_DIR) && $(NPM) install

# -----------------------------------------------------------------------------
# Development Servers
# -----------------------------------------------------------------------------
.PHONY: dev-backend
dev-backend: ## Run FastAPI backend dev server with hot reload
	@echo "==> Starting backend server on http://localhost:8000..."
	cd $(BACKEND_DIR) && $(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run Vite frontend dev server
	@echo "==> Starting frontend server on http://localhost:5173..."
	cd $(FRONTEND_DIR) && $(NPM) run dev

.PHONY: dev
dev: ## Run both backend and frontend concurrently (requires tmux or parallel shells)
	@echo "Please launch backend and frontend in separate terminals:"
	@echo "  make dev-backend"
	@echo "  make dev-frontend"

# -----------------------------------------------------------------------------
# Database & Migrations
# -----------------------------------------------------------------------------
.PHONY: db-migrate
db-migrate: ## Run Alembic migrations against target database
	@echo "==> Applying database migrations..."
	cd $(BACKEND_DIR) && $(UV) run alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback the last Alembic migration
	@echo "==> Rolling back 1 database migration..."
	cd $(BACKEND_DIR) && $(UV) run alembic downgrade -1

.PHONY: db-migration-create
db-migration-create: ## Create a new Alembic migration (usage: make db-migration-create msg="add_column")
	@echo "==> Creating new Alembic revision..."
	cd $(BACKEND_DIR) && $(UV) run alembic revision --autogenerate -m "$(or $(msg),new_migration)"

.PHONY: db-seed
db-seed: ## Seed database with default roles, departments, subjects, and test accounts
	@echo "==> Seeding database..."
	cd $(BACKEND_DIR) && $(UV) run python -m app.db.seed

# -----------------------------------------------------------------------------
# Testing & Code Quality
# -----------------------------------------------------------------------------
.PHONY: test
test: test-backend ## Run all test suites

.PHONY: test-backend
test-backend: ## Run pytest test suite on backend
	@echo "==> Running pytest on backend..."
	cd $(BACKEND_DIR) && $(UV) run pytest app/tests/ -v

.PHONY: test-cov
test-cov: ## Run backend tests with code coverage report
	@echo "==> Running tests with coverage..."
	cd $(BACKEND_DIR) && $(UV) run pytest app/tests/ --cov=app --cov-report=term-missing

.PHONY: lint
lint: lint-backend lint-frontend ## Check code styles and run linters

.PHONY: lint-backend
lint-backend: ## Run ruff linter on backend
	@echo "==> Linting backend with ruff..."
	cd $(BACKEND_DIR) && $(UV) run ruff check .

.PHONY: lint-frontend
lint-frontend: ## Run oxlint / linting on frontend
	@echo "==> Linting frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run lint 2>/dev/null || true

.PHONY: format
format: format-backend ## Format code using ruff
	@echo "==> Formatting code..."

.PHONY: format-backend
format-backend: ## Format Python backend with ruff
	@echo "==> Formatting backend code with ruff..."
	cd $(BACKEND_DIR) && $(UV) run ruff check --fix . && $(UV) run ruff format .

# -----------------------------------------------------------------------------
# Docker & Infrastructure
# -----------------------------------------------------------------------------
.PHONY: docker-up
docker-up: ## Start docker compose production stack
	@echo "==> Launching Docker Compose stack..."
	docker compose -f docker-compose.prod.yml up -d --build

.PHONY: docker-down
docker-down: ## Stop docker compose stack
	@echo "==> Stopping Docker Compose stack..."
	docker compose -f docker-compose.prod.yml down

.PHONY: docker-logs
docker-logs: ## Tail docker compose logs
	docker compose -f docker-compose.prod.yml logs -f

# -----------------------------------------------------------------------------
# Clean & Housekeeping
# -----------------------------------------------------------------------------
.PHONY: clean
clean: ## Remove temporary python cache and build artifacts
	@echo "==> Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf $(BACKEND_DIR)/dist $(BACKEND_DIR)/build $(BACKEND_DIR)/*.egg-info
	rm -rf $(FRONTEND_DIR)/dist
	@echo "==> Clean complete."
