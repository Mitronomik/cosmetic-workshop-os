# Handoff

## Last completed work

PR68 is complete: frontend Alerts workspace has been added.

## Current repo state after PR68

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, backend Alerts, and frontend Alerts UI.

Alerts UI now includes:

- `/alerts` route and `Алерты` navigation item;
- human-readable Russian alert cards for backend-provided message, severity, type, related entity, recommended action, timestamps, and status;
- filters for status, type, and local text search;
- explicit `Обновить алерты` action consuming PR67 `POST /api/alerts/regenerate`;
- explicit resolve and dismiss actions consuming PR67 alert transition endpoints;
- empty/error states that explain the next action.

## Important decisions

- MVP remains local-first and API-first.
- PR68 did not change backend behavior, migrations, alert rules, or API contracts.
- The frontend consumes PR67 backend alert data; it does not calculate alert conditions, stock balances, production readiness, or purchase suggestions.
- No purchase suggestions, automatic notifications, scheduler, cron, polling, dashboard analytics, stock/order/production mutations, import/export, cloud, mobile, auth, roles, or advanced analytics were added.

## Known testing limitations

- Manual browser smoke was not run in this non-interactive environment. Use the checklist from the PR68 prompt when a browser is available.
- FastAPI TestClient-dependent tests may skip automatically when the installed Starlette/httpx combination is unavailable.

## Next recommended task

Purchase suggestions backend foundation is the next recommended roadmap slice.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `npm --prefix frontend run build`
- `git diff --check`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_production_batches_api.py -q`
