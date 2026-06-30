# Handoff

## Last completed work

PR71 frontend Dashboard operational overview has been implemented.

## Current repo state after PR71

Completed foundations include local-first backend/API persistence, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, backend Alerts, frontend Alerts UI, backend Purchase Suggestions, frontend Purchase Suggestions UI, and the frontend operational Dashboard.

Dashboard frontend now includes:

- `/` route with “Сегодня в мастерской” operational overview;
- onboarding checklist preserved on the dashboard;
- frontend-only aggregation over existing APIs/helpers for orders, clients, open alerts, open purchase suggestions, and production batches;
- production-safe loading behavior: the first load shows only the loading state until real dashboard data arrives, manual refresh keeps the previous snapshot visible, and failed refreshes show a soft stale-data message;
- priority cards for active orders, orders waiting for materials, orders ready to produce, open alerts, open purchase suggestions, and recent production;
- “Что сделать сегодня” guidance based on existing alert severity, order statuses, and open purchase suggestions;
- active orders, alerts, purchase suggestions, and recent production sections with compact card rows and empty states;
- quick navigation buttons to orders, ingredients, ingredient lots, packaging, alerts, purchase suggestions, and production;
- backup reminder copy that does not claim backup/export UI is implemented.

## Safety notes

- PR71 is frontend-only and does not add a `GET /api/dashboard` endpoint.
- No backend behavior, migrations, analytics, charts, scheduler, polling, notifications, backup/export implementation, import/export, supplier/procurement automation, stock movement creation, IngredientLot creation, packaging inbound movement, order mutation, production mutation, alert mutation, or purchase suggestion mutation were added.
- Dashboard refresh only reloads existing GET data and keeps previously loaded data visible while a manual refresh is in progress.
- Dashboard does not call alert regeneration, purchase suggestion regeneration, production readiness checks, production confirmation, backup, import, or export endpoints.
- Dashboard does not calculate inventory shortages, production readiness, purchase suggestions, tax, margin, or stock write-off.

## Suggested next work

Next recommended PR: Backup/export UI foundation or Backup/export backend/frontend foundation, depending on the current backup/export backend state.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `npm --prefix frontend run build`
- `git diff --check`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`
- Optional regression checks:
  - `python3 -m pytest backend/app/tests/test_orders.py -q`
  - `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
  - `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
  - `python3 -m pytest backend/app/tests/test_production_batches_api.py -q`

## Manual smoke

Browser smoke was not run in this non-interactive terminal session. Recommended manual smoke checklist for PR71 follow-up:

1. Start backend and frontend.
2. Open `/` with backend running.
3. Confirm first load shows “Загружаем обзор мастерской…” before dashboard data and does not show fake zero metric cards.
4. Confirm dashboard overview appears after data loads.
5. Click “Обновить обзор”.
6. Confirm previous data remains visible while reloading and the reload button shows “Обновляем…”.
7. Stop backend or simulate failed reload.
8. Confirm previous data remains visible with the soft message: “Не удалось обновить обзор. Показываем последние загруженные данные.”
9. Confirm no alert/purchase regeneration occurs.
10. Confirm no readiness/production/backup/import actions occur.
