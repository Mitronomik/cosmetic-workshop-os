# Handoff

## Last completed work

PR66 is complete: read-only production history API and UI have been added.

## Current repo state after PR66

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, and read-only Production History.

Production history now includes:

- `GET /api/production-batches` for newest-first production batch history;
- `GET /api/production-batches/{batch_id}` for full historical batch details;
- `GET /api/orders/{order_id}/production-batch` for locating a produced order's batch after app reload;
- backend responses with order/product/client context plus historical snapshot rows;
- a real frontend `Производство` page with searchable history and a read-only detail panel;
- detail sections for header/source, cost snapshot, consumed ingredient lots, consumed packaging, production note, and safety notes;
- Orders integration that lets produced/delivered orders open the historical batch without exposing production confirmation again.

## Important decisions

- MVP remains local-first and API-first.
- Production history is read-only; no production write, edit, delete, reversal, recalculation, stock movement, or packaging movement logic was added.
- The frontend displays backend snapshots only and does not calculate consumed lots, stock write-offs, costs, tax, or margin.
- No migration was added because existing production batch snapshot tables already support the read UI.

## Known testing limitations

- Manual browser smoke was not run because the environment is non-interactive.
- FastAPI TestClient-dependent tests may skip automatically when the installed Starlette/httpx combination is unavailable.

## Next recommended task

Continue with the next explicitly requested roadmap slice. Keep production reversal/undo, partial production, lot override, reservations, alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, and advanced analytics out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_production_batches_api.py -q`
- `python3 -m pytest backend/app/tests/test_packaging_stock_movements.py -q`
- `python3 -m pytest backend/app/tests/test_stock_movements.py -q`
- `npm --prefix frontend run build`
- `git diff --check`
