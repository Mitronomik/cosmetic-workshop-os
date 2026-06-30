# Handoff

## Last completed work

PR62 is complete: the backend can check whether an existing order is ready for production without mutating stock, packaging, production, or order lifecycle data.

## Current repo state after PR62

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, and backend Production Readiness foundation.

Production readiness now includes:

- `POST /api/orders/{order_id}/check-production-readiness`;
- exact recipe source resolution from `recipe_version_id` or `client_recipe_id`;
- ingredient requirement calculation for the order batch size;
- current ingredient lot balance checks from existing stock movements;
- FEFO lot candidate selection, with dated lots before undated lots;
- expired and soon-expiring selected lot warnings;
- density/conversion warnings when ml↔g conversion cannot be trusted;
- selected packaging balance checks when packaging is present on the order;
- optional cost/tax/margin estimates when available data supports them;
- lifecycle rejection for cancelled, archived, or inactive orders.

The readiness endpoint intentionally does not create stock movements, packaging stock movements, production batch tables/rows, alerts, purchase suggestions, imports/exports, or frontend UI. It does not change order status, `produced_at`, `delivered_at`, recipe versions, client recipe composition, ingredient lots, or packaging items.

## Important decisions

- MVP remains local-first and API-first.
- Readiness is a read-only backend/domain use case, not production confirmation.
- FEFO uses current derived lot balances from immutable movement rows.
- Cost estimates are opportunistic: missing unit costs return null estimates and explicit warnings rather than adding accounting scope.
- Tax estimate currently uses the existing MVP default assumption of 6% when sale price is available; no new settings were added.

## Known testing limitations

- FastAPI `TestClient` tests are skipped automatically if the installed Starlette/httpx combination is unavailable in the environment.
- Frontend browser smoke was not run because PR62 is backend-only.

## Next recommended task

Production confirmation foundation as a new scoped PR: add explicit confirmation, `ProductionBatch` persistence, transactional ingredient/packaging stock write-off, order lifecycle transition, and audit logging only if requested.

Keep alerts, purchase suggestions, production UI, import/export, backup/restore UI, cloud, mobile, OCR, auth, and roles out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_recipes.py -q`
- `python3 -m pytest backend/app/tests/test_stock_movements.py -q`
- `python3 -m pytest backend/app/tests/test_packaging_stock_movements.py -q`
- `git diff --check`
