# Handoff

## Last completed work

PR64 is complete: backend production confirmation foundation has been added.

## Current repo state after PR64

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, and backend Production Confirmation.

Production confirmation now includes:

- `POST /api/orders/{order_id}/produce`;
- explicit `confirm=true` request validation;
- transactional `ProductionConfirmationService`;
- readiness re-check through `ProductionReadinessService` before any write;
- `ProductionBatch`, `ProductionBatchIngredient`, and `ProductionBatchPackaging` persistence;
- historical snapshots of selected ingredient lots and packaging costs/names;
- ingredient lot write-offs through `stock_movements`;
- packaging write-offs through `packaging_stock_movements`;
- order status transition to `produced` with `produced_at` set;
- safe audit entry for production confirmation;
- rollback on failures so no partial batch, movement, or order status update remains.

## Important decisions

- MVP remains local-first and API-first.
- Production confirmation logic lives in backend services, not frontend.
- Production readiness remains read-only.
- Production confirmation does not introduce hidden tax assumptions: tax, margin, and margin percent remain null.
- Existing stock movement trace fields are used for ingredient production write-offs (`reference_type=production_batch`, `reference_id=<batch id>`); packaging write-offs currently store trace context in movement notes because the existing packaging movement schema has no reference fields.
- No frontend production confirmation UI was added.

## Known testing limitations

- FastAPI TestClient tests skip automatically in production confirmation/readiness/order tests when the installed Starlette/httpx combination is unavailable.
- Existing `test_stock_movements.py` still imports TestClient inside the test and fails in this environment because `httpx` is not installed; this pre-existing environment limitation was not changed in PR64.
- Manual browser smoke was not run because this PR is backend-only and the environment is non-interactive.

## Next recommended task

Frontend production confirmation UI as a new scoped PR: add an explicit confirmation action in Orders that calls `POST /api/orders/{order_id}/produce`, refreshes the order/readiness state, and clearly explains that stock will be written off only after confirmation.

Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, partial production, production undo/reversal, and manual lot override UI out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_stock_movements.py -q`
- `python3 -m pytest backend/app/tests/test_packaging_stock_movements.py -q`
- `git diff --check`
