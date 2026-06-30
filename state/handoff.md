# Handoff

## Last completed work

PR61 is complete: the frontend Orders UI foundation lets the user browse, create, inspect, safely edit, cancel, and archive orders through the existing PR60 backend API.

## Current repo state after PR61

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend foundation, and Orders frontend foundation.

Orders UI now includes:

- `Заказы` navigation and `/orders` route;
- human-friendly order list with product, client, recipe source, batch size, packaging, status, planned date, and sale price;
- lightweight search/status filters;
- create order form for active clients and either a base recipe version or an individual client recipe;
- safe edit form that sends only fields accepted by `OrderCreateRequest` / `OrderUpdateRequest`;
- explicit cancel and archive actions with confirmation;
- read-only display for future production statuses.

Orders intentionally still do not create stock movements, packaging stock movements, production batches, readiness calculations, alerts, purchase suggestions, import/export records, cost/tax/margin calculations, or production UI.

## Important decisions

- MVP remains local-first and API-first.
- Orders are historical bridge records and must not mutate `RecipeVersion`, `ClientRecipe`, copied composition rows, inventory movements, or production data.
- The Orders UI never includes controls for `status`, `produced_at`, or `delivered_at`; cancel/archive use dedicated backend endpoints.
- Decimal-backed quantities and money are sent as strings from the UI.
- Sensitive client notes are not surfaced in order audit summaries by frontend changes.

## Known testing limitations

- Frontend manual browser smoke was not run in this non-interactive environment.
- FastAPI `TestClient` tests may be skipped if the installed Starlette/httpx combination is unavailable in the environment.

## Next recommended task

Production readiness foundation for orders.

Keep the next PR narrow: add backend/domain readiness checks and/or a read-only readiness UI only if explicitly scoped. Production confirmation, automatic stock write-off, production batches, alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, and roles remain out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `npm --prefix frontend run build`
- `git diff --check`
