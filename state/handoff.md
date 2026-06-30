# Handoff

## Last completed work

PR60 is complete: the backend Orders foundation persists customer orders and exposes API routes to create, read, list, update, cancel, and archive orders.

## Current repo state after PR60

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, and now orders.

Orders connect an active client to exactly one recipe source (`RecipeVersion` or same-client active `ClientRecipe`) with optional active packaging, target batch size, optional sale price, dates, notes, lifecycle status, archive/cancel semantics, and transactional audit logging.

Orders intentionally do not create stock movements, packaging stock movements, production batches, readiness calculations, alerts, purchase suggestions, import/export records, or frontend UI.

## Important decisions

- MVP remains local-first and API-first.
- Orders are historical bridge records and must not mutate `RecipeVersion`, `ClientRecipe`, copied composition rows, inventory movements, or production data.
- Decimal-backed quantities and money are stored as strings.
- Order writes are service-level transactions; audit failure rolls back the order write.
- Sensitive client notes are not copied into order audit summaries.

## Known testing limitations

- FastAPI `TestClient` tests may be skipped if the installed Starlette/httpx combination is unavailable in the environment.

## Next recommended task

Orders UI foundation.

Keep the next PR narrow: add only frontend/API-client UX needed to browse and manage orders through the existing backend. Production readiness, production confirmation, automatic stock write-off, production batches, alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, and roles remain out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py`
- `python3 -m pytest backend/app/tests launcher/tests`
