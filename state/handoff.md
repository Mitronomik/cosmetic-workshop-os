# Handoff

## Last completed work

PR65 is complete: frontend production confirmation UI has been added to the Orders workspace.

## Current repo state after PR65

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, and frontend Production Confirmation UI.

Production confirmation UI now includes:

- frontend response types for production batch, ingredient write-off snapshots, and packaging write-off snapshots;
- `produceOrder(orderId, notes)` helper using `POST /api/orders/{order_id}/produce` with `confirm=true` only;
- in-memory confirmation state per order;
- readiness-gated `Изготовить` action in the order detail view;
- inline second-confirmation panel explaining that production creates a production batch, writes off components and packaging, and marks the order as produced;
- optional production notes textarea;
- human-readable production success panel displaying returned backend batch details without raw JSON;
- backend refresh after success so the order status is sourced from the API;
- lifecycle guards hiding production actions for cancelled, archived/inactive, delivered, and already produced orders.

## Important decisions

- MVP remains local-first and API-first.
- Production confirmation logic remains in backend services; the frontend only displays backend readiness/results and sends the explicit confirmation request.
- The frontend does not calculate readiness, stock write-offs, lot selection, production batches, tax, margin, or costs.
- Production confirmation remains a destructive action requiring a second explicit user confirmation.
- No migrations or backend production logic changes were made in PR65.

## Known testing limitations

- Manual browser smoke was not run because this environment is non-interactive.
- FastAPI TestClient tests may skip automatically in production confirmation/readiness/order tests when the installed Starlette/httpx combination is unavailable.
- Existing `test_stock_movements.py` may fail in this environment if `httpx` is not installed for TestClient imports; document the exact result when rerun.

## Next recommended task

Production history read UI and production batch detail page.

Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, partial production, production undo/reversal, and manual lot override UI out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `npm --prefix frontend run build`
- `python3 -m pytest backend/app/tests/test_packaging_stock_movements.py -q`
- `python3 -m pytest backend/app/tests/test_stock_movements.py -q`
- `git diff --check`
