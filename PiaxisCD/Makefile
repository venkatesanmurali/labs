.PHONY: setup setup-backend setup-frontend backend frontend test test-backend test-frontend demo db clean

# ─── Setup ────────────────────────────────────────────
setup: setup-backend setup-frontend

setup-backend:
	cd backend && pip install -r requirements.txt

setup-frontend:
	cd frontend && npm install

# ─── Database ─────────────────────────────────────────
db:
	mysql -u root -e "CREATE DATABASE IF NOT EXISTS piaxiscd;" 2>/dev/null || true
	cd backend && alembic upgrade head

db-migrate:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# ─── Run ──────────────────────────────────────────────
backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# ─── Test ─────────────────────────────────────────────
test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npm test -- --run

# ─── Demo ─────────────────────────────────────────────
demo:
	cd backend && python -c "\
from app.services.generation_service import DemoService; \
import json; \
result = DemoService.generate_demo(); \
print(json.dumps(result, indent=2))"

# ─── Clean ────────────────────────────────────────────
clean:
	rm -rf data/demo
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
