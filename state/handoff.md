# Handoff

## Last completed work
Implemented PR5 domain primitives, units and Decimal foundation. The backend now has Decimal-only parsing/quantization helpers, MVP unit definitions, lightweight measurement value objects, reusable domain validation issues/errors, and a database-free ml-to-grams conversion helper that requires explicit density and returns a warning when density is missing.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads plus technical database/settings endpoints from previous PRs. Frontend remains the branded static shell with no new business UI. No recipes, clients, inventory, orders, production, imports, exports, backup UI/restore, cloud, mobile, OCR, auth or roles were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- PR5 adds backend-only domain primitives under `backend/app/domain/` and does not add database tables or migrations.
- Critical numeric parsing rejects floats/bools and expects strings, integers, or `Decimal` to avoid accidental binary-float calculations.
- Quantization rules are explicit: grams/ml to 0.001, percentages/money to 0.01, counts to whole units, density to 0.0001 g/ml, using `ROUND_HALF_UP`.
- Density conversion uses `grams = ml * density`; it does not assume `1 ml = 1 g` when density is missing.
- Missing density returns a structured warning result instead of pretending the conversion is exact.
- Existing database/startup decisions from PR2-PR4 remain unchanged.

## Known issues
- Full backend pytest currently fails in this environment because FastAPI is not installed.
- `make test` has the same FastAPI dependency limitation because it runs full backend tests.
- API endpoint smoke with FastAPI TestClient cannot be completed until backend dependencies are installed.

## Next recommended task
Proceed to the next roadmap-scoped task after PR5 review/merge. Do not add business entities, migrations, or CRUD until explicitly scoped by the next task.

## Commands run
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app -name '*.py')`
- `cd backend && python3 -m pytest app/tests/test_domain_primitives.py`
- `cd backend && python3 -m pytest`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`

## Tests status
Python syntax compilation passed. Scoped domain primitive tests passed. Frontend build and `make build` passed. Full backend pytest and `make test` are blocked by the environment because FastAPI is not installed; this is not caused by PR5 domain primitive assertions.
