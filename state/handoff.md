# Handoff

## Last completed work
Implemented PR4 backup-before-migration foundation. The backend now has a backup service that safely copies an existing SQLite database into the user-data `backups/` directory, returns minimal backup metadata, fails clearly for missing sources, and avoids overwriting existing backup files. Explicit user-mode startup now creates a `before_migration` backup only when an existing user database has pending migrations.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads plus technical database/settings endpoints from PR2. Frontend remains the branded static shell from PR1b with no new business UI. No recipes, clients, inventory, orders, production, imports, exports, backup UI/restore, cloud, mobile, OCR, auth or roles were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- Default local development DB path remains repository-root `.local/cosmetic_workshop.sqlite`, which is gitignored and stable across current working directories.
- `COSMETIC_WORKSHOP_DB_PATH` remains the development/explicit database file override.
- User-mode data directory defaults to `~/Documents/Мастерская косметолога/` and can be overridden with `COSMETIC_WORKSHOP_USER_DATA_DIR`.
- User-mode backup files are stored in `backups/` under that user data directory.
- User-mode database path resolves to `data/cosmetic_workshop.sqlite` inside the user data directory.
- Directory creation and migrations are explicit startup actions; ordinary GET/read endpoints must not create directories, initialize a database, create backups, or apply migrations as side effects.
- Backup-before-migration currently runs only in explicit user-mode startup for existing database files with pending migrations; brand-new user-mode startup does not create backup files.
- Startup mode validation accepts only `development` and `user`; unsupported modes raise `ValueError` before filesystem/database side effects.
- Migration metadata is stored in `schema_migrations`.
- Initial migration creates only `app_settings` and `audit_logs`, plus indexes and metadata.

## Known issues
- `python3 -m pip install -e "backend[test]"` failed in the current environment because registry/proxy access to setuptools was blocked with `Tunnel connection failed: 403 Forbidden`.
- `cd backend && python3 -m pytest` currently fails in this environment because FastAPI is not installed. This is environmental/dependency availability, not a test assertion failure.
- API endpoint smoke with FastAPI TestClient cannot be completed until backend dependencies are installed.

## Next recommended task
Proceed to the next roadmap-scoped foundation task after PR4 review/merge. Keep business entities out until their PRs are explicitly scoped. A future launcher/package runtime PR should call explicit startup initialization in user mode; backup-before-migration is now available for that path.

## Commands run
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app -name '*.py')`
- `cd backend && python3 -m pytest`
- `PYTHONPATH=backend python3 - <<'PY' ...` temporary backup/startup smoke
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`

## Tests status
Python syntax compilation passed. Temporary-directory backup/startup smoke passed without touching real user directories. Frontend build status is recorded in the PR summary. Backend pytest and FastAPI endpoint smoke are blocked until backend dependencies are installed because package registry/proxy access is unavailable in the current environment.
