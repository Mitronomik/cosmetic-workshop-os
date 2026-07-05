# Handoff

## Last completed work

PR74 — Backup UI — has been implemented.

## Current repo state after PR74

Completed foundations include local-first backend/API persistence, user data directory foundation, SQLite backup service, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, backend Alerts, frontend Alerts UI, backend Purchase Suggestions, frontend Purchase Suggestions UI, the operational Dashboard, PR72 Orders UX hotfix, PR73 manual backup API foundation, and PR74 frontend Backup UI.

PR74 frontend changes include:

- `/backups` route and «Резервные копии» navigation item;
- backup API helpers for `GET /api/backups/status`, `GET /api/backups`, and explicit-click `POST /api/backups`;
- a human-readable backup workspace showing database path/existence/size, backup directory path/existence, backup count, latest backup, backup history, local file paths, and clear safety copy;
- explicit manual backup creation with reason presets and a max-80-character custom reason;
- success/error/loading states and a refreshed backup list after successful creation;
- dashboard backup reminder now links to `/backups`.

## Safety notes

- PR74 consumes the PR73 API only and does not change backend behavior.
- Page load and reload call only `GET /api/backups/status` and `GET /api/backups`.
- `POST /api/backups` is called only after an explicit user action on the backup page.
- No restore, download, delete, scheduled backups, cloud backup, export, import, arbitrary source/destination path input, polling, notifications, backend endpoints, migrations, or backup automation were added.
- No recipes, clients, orders, stock, production batches, alerts, purchase suggestions, or other business records are mutated by this UI.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `npm --prefix frontend run build`
- `git diff --check`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_backups_api.py -q`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`

## Manual smoke

Manual browser smoke was not run in this non-interactive session because starting and exercising long-running backend/frontend servers in a browser was not practical here. Recommended PR74 manual smoke checklist:

1. Start backend and frontend.
2. Open app and then `/backups`.
3. Confirm page loads without crash.
4. Confirm status cards show database path, backup dir, database exists/missing state, backup count, and latest backup.
5. Confirm missing backup dir is shown as a normal empty state.
6. Confirm backup list loads or shows the clear empty state.
7. Select `manual`, click `Создать резервную копию`, and confirm success message plus filename.
8. Create a second backup and confirm the first remains.
9. Select custom reason and confirm it is accepted safely.
10. Confirm there are no restore/download/delete buttons.
11. Confirm dashboard reminder navigates to `/backups`.
12. Confirm opening `/backups` and clicking `Обновить` do not create backups automatically.
13. Confirm recipes, clients, orders, stock, production, alerts, and purchase suggestions are unchanged.

## Next recommended PR

Export foundation or Import/Export preparation, depending on the next roadmap slice.
