# Handoff

## Last completed work

PR76 — Export UI — has been implemented.

## Current repo state after PR76

The frontend now has a real `/exports` workspace reachable from the “Экспорт” navigation item under “Данные и настройки”. The page consumes only the PR75 Export API:

- `GET /api/exports/status` for database/export directory status;
- `GET /api/exports` for read-only local JSON export history;
- `POST /api/exports` only after the user explicitly clicks/submits “Создать экспорт”.

The UI includes:

- local-first intro and safety copy explaining JSON export snapshots;
- status cards for database existence/path/size, export directory, export count, and latest export;
- manual export creation with reason presets and a max-80-character custom reason;
- success/error messaging and created filename display;
- backend-provided entity count summary after successful export creation;
- export history list showing filename, date, size, reason, and local path;
- explicit “Пока не реализовано” card for import, restore, download, CSV/XLSX, PDF reports, scheduled export, and cloud export.

## Safety notes

- Page load and explicit reload call only GET export endpoints.
- No export is created automatically on page load or reload.
- No import, restore, download, delete, rename, verification, CSV/XLSX, PDF/report, scheduled export, cloud export, polling, notifications, dashboard analytics, or arbitrary path input was added.
- No backend endpoints, migrations, or business-entity mutations were added.
- The frontend does not inspect JSON export files or infer entity counts; it displays backend response data only.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `npm --prefix frontend run build`
- `git diff --check`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_exports_api.py -q`
- `python3 -m pytest backend/app/tests/test_backups_api.py -q`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`

## Manual smoke

Manual browser smoke was not run in this non-interactive session because starting and exercising long-running backend/frontend servers through a browser is not practical here. Recommended PR76 smoke:

1. Start backend and frontend.
2. Open `/exports`.
3. Confirm status/list load and no export is created automatically.
4. Create exports with `manual` and custom reasons.
5. Confirm success message, entity counts, and history reload.
6. Confirm there are no import/restore/download/delete buttons.
7. Confirm Backup page and Dashboard still open.

## Next recommended PR

Import CSV/XLSX draft backend foundation.
