# JSON Export Foundation

PR75 adds a backend-only local JSON export foundation for **Мастерская косметолога**.

## Purpose

The export API lets the user explicitly create a local JSON snapshot of the main workshop data before import preparation, data transfer checks, or support review.

Export is not backup and does not replace backup. Backup preserves the SQLite database file. Export creates a readable JSON snapshot of whitelisted domain tables.

## Local directory

Exports are written under the selected local `exports/` directory:

```text
~/Documents/Мастерская косметолога/exports/
```

In development and tests, when the configured database is not the user data database, exports are written next to the configured SQLite database:

```text
/path/to/dev-db-parent/exports/
```

This prevents tests and local development from accidentally writing to the real user Documents directory.

## API

PR75 adds:

```http
GET  /api/exports/status
GET  /api/exports
POST /api/exports
```

`GET` endpoints are read-only. They do not create directories, databases, export files, backups, migrations, imports, restores, stock movements, production batches, alerts, or purchase suggestions.

`POST /api/exports` is explicit. It may create the `exports/` directory and writes one new JSON file. Existing exports are never overwritten.

## JSON shape

Each export file contains:

```json
{
  "manifest": {
    "export_schema_version": 1,
    "created_at": "2026-07-05T12:00:00Z",
    "reason": "manual",
    "source": "cosmetic-workshop-os",
    "database_filename": "cosmetic_workshop.sqlite",
    "database_location_kind": "user_data",
    "tables": {
      "ingredients": 12,
      "ingredient_lots": 3
    }
  },
  "data": {
    "ingredients": [],
    "ingredient_lots": []
  }
}
```

The export file intentionally does not store the absolute local database path. API status responses may show local paths for the local UI, but exported JSON snapshots use portable source metadata.

IDs and relationship fields are preserved as stored in SQLite. Date/time values are exported as stored strings or ISO-compatible JSON values. Decimal-like values remain the app's stored string values; decimal localization is UI-only.

## Exported entity groups

The export service uses an explicit whitelist and skips whitelisted tables that do not exist in the current database. Current groups include:

- app settings;
- ingredients and ingredient lots;
- ingredient stock movements;
- packaging items and packaging stock movements;
- catalog categories and catalog tags;
- ingredient, packaging, and recipe tag assignment tables;
- recipe templates, recipe versions, and recipe ingredients;
- clients, client recipes, client recipe ingredients, wishes, and feedback;
- orders;
- production batches, ingredients, and packaging lines;
- alerts;
- purchase suggestions;
- audit logs.

SQLite internals and migration metadata such as `schema_migrations` or `alembic_version` are not exported.

## Safety boundaries

PR75 does not add:

- frontend UI;
- import;
- restore;
- CSV/XLSX/PDF export;
- download endpoint;
- delete endpoint;
- arbitrary source path;
- arbitrary destination path;
- scheduled exports;
- cloud export;
- reports or analytics.

The export API never reads arbitrary filesystem contents and never includes files from `backups/`, `exports/`, `attachments/`, or `logs/`.

## Testing

Automated tests use `tmp_path` and monkeypatch `COSMETIC_WORKSHOP_DB_PATH` and, where needed, `COSMETIC_WORKSHOP_USER_DATA_DIR`. Tests must not write to the real `~/Documents/Мастерская косметолога/` directory.
