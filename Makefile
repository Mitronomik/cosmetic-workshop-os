.PHONY: setup dev run-local test build test-backend build-frontend package-macos smoke

setup:
	python3 -m pip install -e "backend[test]"
	cd frontend && npm install

dev:
	@echo "Start backend: cd backend && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
	@echo "Start frontend in another terminal: cd frontend && npm run dev"

run-local:
	python3 -m launcher.main --no-browser

test: test-backend

test-backend:
	python3 -m pytest

build: build-frontend

build-frontend:
	cd frontend && npm run build

package-macos:
	@echo "TODO: implement macOS packaging in a future PR"

smoke:
	@echo "Run current smoke manually: backend health endpoints, database status/settings endpoints, temporary SQLite migrations, frontend build."
