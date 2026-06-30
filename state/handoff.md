# Handoff

## Last completed work

PR67 is complete: backend Alert engine foundation has been added.

## Current repo state after PR67

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, and backend Alerts.

Alerts now include:

- `alerts` table with unique `alert_key` for deduplication;
- backend generation service for low ingredient stock, low packaging stock, expiring ingredient lots, expired ingredient lots, insufficient materials for active orders, and insufficient packaging for active orders;
- `GET /api/alerts` with status/type/pagination filters;
- `POST /api/alerts/regenerate` for explicit regeneration;
- `POST /api/alerts/{alert_id}/resolve` and `POST /api/alerts/{alert_id}/dismiss`;
- status history preservation: alerts are not deleted, open alerts are resolved when conditions disappear, and resolved/dismissed alerts are not reopened in PR67;
- tests for idempotency, deduplication, status transitions, alert types, and read-only guarantees.

## Important decisions

- MVP remains local-first and API-first.
- Alert generation is explicit; no scheduler, cron, background worker, notification channel, purchase suggestion, dashboard widget, or frontend page was added.
- Alert generation may mutate only `alerts`; it must not mutate orders, production batches, stock movements, packaging movements, ingredient lots, ingredients, packaging items, recipes, or clients.
- Order shortage alerts are order-level alerts, not one alert per missing ingredient/package item.
- Resolved/dismissed alerts are not reopened automatically in PR67.

## Known testing limitations

- Manual browser smoke was not required because PR67 is backend-only.
- FastAPI TestClient-dependent tests may skip automatically when the installed Starlette/httpx combination is unavailable.

## Next recommended task

Continue with the next explicitly requested roadmap slice. Keep alert frontend UI, dashboard widgets, purchase suggestions, external notifications, schedulers, production reversal/undo, partial production, lot override, reservations, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, and advanced analytics out of scope unless explicitly requested.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_production_batches_api.py -q`
- `python3 -m pytest backend/app/tests/test_packaging_stock_movements.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`
- `python3 -m pytest backend/app/tests/test_stock_movements.py -q`
- `npm --prefix frontend run build`
- `git diff --check`
