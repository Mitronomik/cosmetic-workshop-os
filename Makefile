.PHONY: setup setup-backend setup-frontend dev run-local test build test-backend build-frontend package-macos smoke

setup: setup-backend setup-frontend

setup-backend:
	python3 -m pip install -e "backend[test]"

setup-frontend:
	cd frontend && npm install

dev:
	@echo "Start backend: cd backend && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
	@echo "Start frontend in another terminal: cd frontend && npm run dev"

run-local:
	python3 -m launcher.main --no-browser

test: test-backend

test-backend: setup-backend
	python3 -m pytest backend/app/tests launcher/tests

build: build-frontend

build-frontend:
	cd frontend && npm run build

package-macos:
	@echo "TODO: implement macOS packaging in a future PR"

smoke:
	@echo "Run current smoke manually: backend health endpoints, database status/settings endpoints, temporary SQLite migrations, frontend build."
