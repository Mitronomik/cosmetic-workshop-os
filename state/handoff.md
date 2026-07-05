# Handoff

## Last completed work

PR73 — Manual Backup API foundation — has been implemented.

## Current repo state after PR73

Completed foundations include local-first backend/API persistence, user data directory foundation, SQLite backup service, ingredients/lots, stock movements, packaging and packaging movements, inventory reads, recipe templates/versions/calculation, clients, client recipes and copied composition editing/restoring, client wishes/feedback, Orders backend/UI foundations, backend Production Readiness, Orders readiness UI, backend Production Confirmation, frontend Production Confirmation UI, read-only Production History, backend Alerts, frontend Alerts UI, backend Purchase Suggestions, frontend Purchase Suggestions UI, the operational Dashboard, PR72 Orders UX hotfix, and PR73 manual backup API foundation.

PR73 backend changes include:

- `GET /api/backups/status` reports current database path/existence/size, selected backup directory/existence, backup count, and latest backup metadata;
- `GET /api/backups` lists existing SQLite-like backup files newest first and treats a missing backup directory as an empty list;
- `POST /api/backups` explicitly creates a local SQLite backup using the existing backup service and returns safe metadata plus `Резервная копия создана.`;
- backup path selection uses the resolved user backup directory only when the current database is the resolved user database path or `COSMETIC_WORKSHOP_USER_DATA_DIR` is explicitly set; otherwise development backups stay next to the configured database;
- backup reasons are trimmed, blank reasons become `manual`, reasons over 80 characters are rejected, and unsafe filename characters are sanitized by the backup service.

## Safety notes

- No restore, backup UI, scheduled backups, cloud backup, CSV/XLSX export, database download endpoint, backup deletion/rename/compression/encryption, migrations, frontend navigation, supplier/procurement features, analytics, polling, notifications, or app packaging changes were added.
- GET backup endpoints are read-only and do not create backup directories, backup files, database files, migrations, imports, exports, orders, stock movements, production batches, alerts, or purchase suggestions.
- POST backup does not accept arbitrary source or destination paths; it copies only the currently configured SQLite database and never overwrites an existing backup.
- Tests use temporary paths via environment overrides and must not write to the real `~/Documents/Мастерская косметолога/` directory.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_backups_api.py -q`
- `python3 -m pytest backend/app/tests/test_database_foundation.py -q`
- `python3 -m pytest backend/app/tests/test_orders.py -q`
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q`
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q`
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q`
- `python3 -m pytest backend/app/tests/test_alerts.py -q`
- `npm --prefix frontend run build`
- `git diff --check`

## Manual smoke

Manual backend smoke was not run because this non-interactive PR session used automated tests only and did not start a long-running local backend server. Recommended PR73 manual smoke checklist:

1. Start backend with a temporary or intended local database path.
2. Confirm current DB exists.
3. Call `GET /api/backups/status`.
4. Confirm it returns current database path and backup dir.
5. Confirm status GET does not create a backup file.
6. Call `GET /api/backups`.
7. Confirm it returns existing backups or an empty list.
8. Call `POST /api/backups` with `{ "reason": "manual" }`.
9. Confirm response says backup was created.
10. Confirm a new backup file appears in backup dir.
11. Confirm source DB still exists and was not modified.
12. Call `POST /api/backups` again.
13. Confirm a second unique backup file is created and the first is not overwritten.
14. Call `GET /api/backups`.
15. Confirm both backups appear newest first.
16. Point DB path to a missing temp file.
17. Confirm `POST /api/backups` returns the safe missing DB error.
18. Confirm no restore/import/export/stock/order/production changes are possible through this API.

## Next recommended PR

PR74 — Backup UI.
