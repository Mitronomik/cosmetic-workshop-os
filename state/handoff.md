# Handoff

## Last completed work
Implemented PR2 database, migrations, settings and audit foundation. The backend now has SQLite connection/session helpers, a small migration runner, an initial infrastructure migration, seeded app-level settings, audit log table structure, and thin technical endpoints for `/api/database/status` and `/api/settings`. The follow-up stabilized the default DB path and removed hidden migration side effects from read/status endpoints. Existing `/health` and `/api/health` response shape is preserved.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads plus technical database/settings endpoints. Frontend remains the branded static shell from PR1b with no new business UI. No recipes, clients, inventory, orders, production, imports, exports, backups, cloud, mobile, OCR, auth or roles were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the PR2 persistence foundation.
- Default local development DB path is repository-root `.local/cosmetic_workshop.sqlite`, which is gitignored and stable across current working directories. This is intentionally not the final user data directory behavior.
- Migration metadata is stored in `schema_migrations`.
- Database initialization is explicit; GET/read endpoints must not create or migrate the database as a side effect.
- Initial migration creates only `app_settings` and `audit_logs`, plus indexes and metadata.
- App settings values that may later affect decimal-sensitive domains, such as tax rate, are stored as strings/placeholders in this PR.

## Known issues
- `python3 -m pip install -e "backend[test]"` failed in the current environment because registry/proxy access to setuptools was blocked with `Tunnel connection failed: 403 Forbidden`.
- `cd backend && python3 -m pytest` currently fails in this environment because FastAPI is not installed. This is environmental/dependency availability, not a test assertion failure.
- Backend startup smoke cannot be completed until backend dependencies are installed.

## Next recommended task
Proceed to the next roadmap-scoped foundation task after PR2 review/merge. Keep business entities out until their PRs are explicitly scoped. A future user-data-directory PR should move runtime SQLite storage outside the repository/application directory before real user data is stored.

## Commands run
- `python3 -m pip install -e "backend[test]"`
- `python3 -m py_compile $(find backend/app -name '*.py')`
- `cd backend && python3 -m pytest`
- `PYTHONPATH=backend python3 - <<'PY' ...` temporary SQLite explicit initialization/read-status smoke
- `git status --short`
- `git branch --show-current`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`

## Tests status
Python syntax compilation passed. Frontend build passed. Backend pytest and backend startup smoke are blocked by missing FastAPI after dependency installation failed due registry/proxy restrictions.
