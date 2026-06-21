# Handoff

## Last completed work
Implemented PR7 local runtime launcher MVP foundation. Added `launcher.config`, `launcher.runtime`, and `launcher.main` with safe localhost defaults, explicit user-mode startup initialization, backend process launch support, optional browser opening, and clear startup/port-conflict messages. Added launcher tests and developer docs.

Previously applied PR6 hotfix for database foundation tests after ingredients migration. Updated `test_database_foundation.py` so startup/database assertions use the PR6 allowed table set and keep forbidden future business tables excluded.

Previously implemented PR6 ingredients foundation. The backend now has an `ingredients` table migration, ingredient category/unit/name/density domain validation, create/read/list/update/deactivate repository and service methods, thin `/api/ingredients` endpoints with full update exposed as PUT, not partial PATCH, and minimal ingredient audit events.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads plus technical database/settings endpoints from previous PRs. Frontend remains the branded static shell with no new business UI. No ingredient lots, stock movements, packaging, recipes, clients, orders, production, imports, exports, backup UI/restore, cloud, mobile, OCR, auth or roles were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- PR5 adds backend-only domain primitives under `backend/app/domain/`.
- PR6 adds only the `ingredients` business table; forbidden future business tables remain absent. Full ingredient update is `PUT /api/ingredients/{id}`; PATCH is intentionally not exposed.
- Critical numeric parsing rejects floats/bools and expects strings, integers, or `Decimal` to avoid accidental binary-float calculations.
- Quantization rules are explicit: grams/ml to 0.001, percentages/money to 0.01, density to 0.0001 g/ml, using `ROUND_HALF_UP`; counts must already be whole numbers and fractional pieces/items raise validation instead of rounding.
- Density conversion uses `grams = ml * density`; it does not assume `1 ml = 1 g` when density is missing.
- Missing density returns a structured warning result instead of pretending the conversion is exact.
- Existing database/startup decisions from PR2-PR4 remain unchanged.

## Known issues
- Backend tests that import FastAPI still fail in this environment because FastAPI is not installed.
- Attempting `python3 -m pip install -e "backend[test]"` is blocked by the package registry/proxy with `Tunnel connection failed: 403 Forbidden`.
- `make test` has the same dependency limitation because it runs full backend tests.

## Next recommended task
Proceed to the next roadmap-scoped task after PR7 review/merge. Do not add IngredientLot, StockMovement, packaging, recipes, clients, orders, production, imports, frontend UI, or purchase logic until explicitly scoped by the next task.

## Commands run
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app -name '*.py')`
- `cd backend && python3 -m pytest app/tests/test_domain_primitives.py`
- `python3 -m pip install -e "backend[test]"`
- `cd backend && python3 -m pytest app/tests/test_ingredients.py app/tests/test_database_foundation.py`
- `cd backend && python3 -m pytest`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`
- PR6 hotfix reran required checks; backend pytest remains blocked by missing FastAPI and dependency installation remains blocked by registry/proxy 403.

## Tests status
Python syntax compilation passed. Scoped domain primitive tests passed before PR6 and should remain independent of FastAPI. PR6 non-API smoke can be run against a temporary SQLite database without real user data. Full backend pytest and `make test` are blocked by the environment because FastAPI is not installed and dependency installation is blocked by registry/proxy 403 responses; this is not caused by PR6 assertions.

## PR7 notes
- Run launcher MVP with `python3 -m launcher.main --no-browser` or `make run-local` in developer mode.
- Launcher default mode is `user` and respects `COSMETIC_WORKSHOP_USER_DATA_DIR`; tests use temporary directories and do not touch the real Documents folder.
- Static frontend serving/final user package remain follow-up work.
