# Handoff

## Last completed work

PR75 — Export API foundation — has been implemented.

## Current repo state after PR75

Completed foundations include local-first backend/API persistence, user data directory foundation, SQLite backup service and Backup UI, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, backend Alerts, frontend Alerts UI, backend Purchase Suggestions, frontend Purchase Suggestions UI, the operational Dashboard, PR72 Orders UX hotfix, PR73 manual backup API foundation, PR74 frontend Backup UI, and PR75 backend Export API foundation.

PR75 backend changes include:

- `GET /api/exports/status` for read-only export/database status;
- `GET /api/exports` for read-only local JSON export listing;
- `POST /api/exports` for explicit local JSON snapshot creation;
- safe export path resolution for user-data mode and development/test mode;
- whitelisted SQLite table export into `{ manifest, data }` JSON files, including catalog categories/tags and tag assignment tables;
- portable manifest source metadata with `database_filename` and `database_location_kind` instead of an absolute database path inside export files;
- non-overwriting export filenames with normalized reason and safe filename sanitization;
- tests using temporary directories only;
- API and export documentation updates.

## Safety notes

- PR75 does not add frontend UI.
- No import, restore, download, delete, CSV/XLSX/PDF export, scheduled export, cloud export, arbitrary path input, migrations, or backup creation was added.
- `GET /api/exports/status` and `GET /api/exports` do not create databases, directories, files, backups, exports, migrations, or business records.
- `POST /api/exports` writes only a new JSON file under the selected `exports/` directory and never overwrites existing exports.
- Export reads whitelisted SQLite tables only and does not mutate recipes, clients, orders, stock, lots, packaging, production, alerts, purchase suggestions, settings, or audit logs.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_exports_api.py -q`
- `python3 -m pytest backend/app/tests/test_backups_api.py -q`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`
- `npm --prefix frontend run build`
- `git diff --check`

## Manual smoke

Manual browser/API smoke was not run in this non-interactive session because starting and exercising long-running backend/frontend servers manually was not practical here. Recommended PR75 manual smoke checklist:

1. Start backend.
2. Confirm current DB exists.
3. Call `GET /api/exports/status`.
4. Confirm it returns DB path and export dir.
5. Confirm status GET does not create export file.
6. Call `GET /api/exports`.
7. Confirm it returns existing exports or empty list.
8. Call `POST /api/exports` with `{ "reason": "manual" }`.
9. Confirm response says export was created.
10. Confirm a new JSON file appears in export dir.
11. Open JSON file and confirm it has `manifest` and `data`.
12. Confirm manifest includes entity counts.
13. Confirm source DB still exists and was not modified.
14. Call `POST /api/exports` again.
15. Confirm second unique export file is created and first is not overwritten.
16. Call `GET /api/exports`.
17. Confirm both exports appear newest first.
18. Point DB path to missing temp file.
19. Confirm `POST /api/exports` returns safe missing DB error.
20. Confirm no import/restore/download/delete endpoints exist.
21. Confirm no recipes, clients, orders, stock, production, alerts, or purchase suggestions are changed.

## Next recommended PR

PR76 — Export UI.
