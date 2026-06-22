.PHONY: setup setup-backend setup-frontend check-backend-test-deps dev run-local test build test-backend test-backend-with-setup build-frontend package-macos smoke

setup: setup-backend setup-frontend

setup-backend:
	python3 -m pip install -e "backend[test]"

setup-frontend:
	cd frontend && npm install

check-backend-test-deps:
	python3 -c "import pytest; from fastapi.testclient import TestClient; version = tuple(int(part) for part in pytest.__version__.split('.')[:2]); assert (8, 0) <= version < (9, 0), f'pytest {pytest.__version__} is outside pytest>=8,<9'; print(f'backend test dependencies OK: pytest {pytest.__version__}, TestClient {TestClient.__name__}')"

dev:
	@echo "Start backend: cd backend && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
	@echo "Start frontend in another terminal: cd frontend && npm run dev"

run-local:
	python3 -m launcher.main --no-browser

test: test-backend

test-backend:
	python3 -m pytest backend/app/tests launcher/tests

test-backend-with-setup: setup-backend test-backend

build: build-frontend

build-frontend:
	cd frontend && npm run build

package-macos:
	@echo "TODO: implement macOS packaging in a future PR"

smoke:
	@echo "Run current smoke manually: backend health endpoints, database status/settings endpoints, temporary SQLite migrations, frontend build."
