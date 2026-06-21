.PHONY: setup dev test build test-backend build-frontend package-macos smoke

setup:
	python3 -m pip install -e "backend[test]"
	cd frontend && npm install

dev:
	@echo "Start backend: cd backend && python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
	@echo "Start frontend in another terminal: cd frontend && npm run dev"

test: test-backend

test-backend:
	cd backend && python3 -m pytest

build: build-frontend

build-frontend:
	cd frontend && npm run build

package-macos:
	@echo "TODO: implement macOS packaging in a future PR"

smoke:
	@echo "Run PR1 smoke manually: backend /api/health, frontend build, navigation placeholders."
