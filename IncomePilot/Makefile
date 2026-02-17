.PHONY: help install install-backend install-frontend dev backend frontend test test-backend test-frontend lint db-create

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Install ───────────────────────────────────────────────────────────────

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install Python backend deps
	cd backend && python -m pip install -r requirements-dev.txt

install-frontend: ## Install Node frontend deps
	cd frontend && npm install

# ── Database ──────────────────────────────────────────────────────────────

db-create: ## Create the MySQL database (run once)
	mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS incomepilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# ── Dev servers ───────────────────────────────────────────────────────────

dev: ## Start both backend and frontend (needs two terminals, or use &)
	@echo "Run 'make backend' in one terminal and 'make frontend' in another."

backend: ## Start FastAPI dev server on :8000
	cd backend && uvicorn app.main:app --reload --port 8000

frontend: ## Start Vite dev server on :5173
	cd frontend && npm run dev

# ── Test ──────────────────────────────────────────────────────────────────

test: test-backend test-frontend ## Run all tests

test-backend: ## Run pytest
	cd backend && python -m pytest -v

test-frontend: ## Run vitest
	cd frontend && npx vitest run

# ── Lint ──────────────────────────────────────────────────────────────────

lint: ## Lint backend (ruff + black) and frontend (eslint)
	cd backend && ruff check . && black --check .
	cd frontend && npx eslint .
