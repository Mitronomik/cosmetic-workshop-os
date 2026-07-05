# Current focus

PR73 — Manual Backup API foundation is implemented.

## Completed in PR73
- Added backend-only manual backup API endpoints: `GET /api/backups/status`, `GET /api/backups`, and `POST /api/backups`.
- Reused the existing SQLite backup service for explicit backup creation so source database files are copied without mutation and existing backups are not overwritten.
- Added backup metadata schemas and service helpers for safe path selection, backup listing, timestamp parsing, reason normalization, and SQLite-like file filtering.
- Added backend tests for read-only status/list behavior, missing directories, malformed filenames, explicit backup creation, unique backup filenames, missing database errors, and reason validation/sanitization.
- Updated backup/API/state documentation.

## Out of scope / not added
- No restore, backup UI, scheduled backups, cloud backup, export files, import/export, database download, backup deletion/rename, migrations, frontend navigation, business-table mutation, orders, stock, production, alerts, or purchase suggestions were added.

## Next recommended PR
- PR74 — Backup UI.
