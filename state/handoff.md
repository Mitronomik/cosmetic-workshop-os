# Handoff

## Last completed work

PR63 is complete: the Orders frontend now exposes the existing read-only Production Readiness check to the user.

## Current repo state after PR63

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness foundation, and Orders readiness UI.

Production readiness now includes:

- `POST /api/orders/{order_id}/check-production-readiness` on the backend;
- a `Проверить изготовление` button in active order details;
- frontend in-memory readiness state per order;
- human-readable summary for ready/warning/blocked results;
- blocking issue and warning sections using backend messages;
- ingredient requirement table with required, available, missing, fulfillment status, and backend-selected FEFO lots;
- packaging availability table or a clear no-packaging-needed message;
- optional estimated cost, tax, and margin display, with null values shown as `Не рассчитано`;
- safety copy that the check does not write off stock, reserve lots, create production batches, or mutate order status.

The readiness UI intentionally does not calculate ingredient availability, select lots, calculate tax/margin, create stock movements, create packaging movements, create production batches, reserve lots, or mutate order lifecycle state.

## Important decisions

- MVP remains local-first and API-first.
- Frontend displays backend readiness results and does not duplicate production-readiness business logic.
- Readiness remains a read-only workflow; production confirmation is still a future explicit step.
- Tax/margin remain backend-owned. The frontend shows `Не рассчитано` for null estimates and relies on backend warnings for the reason.

## Known testing limitations

- Manual browser smoke was not run in this non-interactive environment.
- FastAPI `TestClient` tests may skip automatically if the installed Starlette/httpx combination is unavailable in the environment.

## Next recommended task

Production confirmation backend foundation as a new scoped PR: add explicit confirmation, `ProductionBatch` persistence, transactional ingredient/packaging stock write-off, order lifecycle transition, and audit logging only if requested.

Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, and roles out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `npm --prefix frontend run build`
- `git diff --check`
