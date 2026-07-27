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

## Canonical filename reason contract (CR-005, decided 2026-07-27)

`CR-005` is **accepted**. This section is the durable product contract for the export filename reason segment. It is a **decision record**: at the time it was written the runtime still produced the older one-underscore-per-character output, and the correcting implementation slice `R4` was authorized but not implemented. See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

### Human manifest reason versus canonical filename reason

Exports carry **two distinct** reason representations, and they must not be conflated:

| Representation | Where it appears | Value |
|---|---|---|
| **Human reason** | the export JSON manifest `reason` field | the normalized user-supplied reason — `text = (reason or "manual").strip() or "manual"` |
| **Canonical filename reason segment** | the filename, and the `reason` field of the create/list/status API responses and the UI | a canonical, path-safe, unambiguous slug derived from the human reason |

Worked example for the input `before-import`:

- filename reason segment: `before_import`
- API create/list/status `reason`: `before_import`
- visible UI reason: `before_import`
- export manifest `reason`: `before-import`

The export manifest continues to preserve the **normalized human reason**, not the filename slug. The export schema version is **not** changed by this decision.

### Canonical algorithm

Identical to the backup contract in `docs/backup-and-restore.md`, and owned by one shared backend helper:

1. preserve Unicode alphanumeric characters exactly;
2. treat underscore as a separator;
3. treat every non-alphanumeric character as a separator — whitespace, hyphen, dot, slash, backslash, punctuation, and symbols;
4. collapse every maximal run of separators into one underscore;
5. remove leading and trailing underscores;
6. when the result is empty, use `manual`;
7. when the result contains only digits, prefix it with `reason_` — for example `123` → `reason_123`;
8. preserve letter case;
9. preserve Unicode alphanumerics — no lowercasing and no transliteration;
10. no new length limit. The existing 80-character request-level limit on `reason` is unchanged.

| Human reason | Canonical filename reason segment |
|---|---|
| `before/import ../unsafe` | `before_import_unsafe` |
| `before-import` | `before_import` |
| `___before---import___` | `before_import` |
| `перед обновлением` | `перед_обновлением` |
| `123` | `reason_123` |
| whitespace only | `manual` |
| punctuation only | `manual` |

Literal hyphens are normalized to underscores inside the filename reason segment, and a segment is never purely numeric. Both rules exist so that the reason segment cannot be confused with the structural hyphens of the filename grammar or with the numeric uniqueness suffix. Hyphens remain fully allowed in the human manifest reason.

### Filename grammar

The existing grammar is preserved. No new filename version, marker, sidecar format, or migration is authorized. A new export filename remains conceptually:

```text
{timestamp}-cosmetic_workshop-export-{canonical_reason}[-N].json
```

where `canonical_reason` contains no hyphen and is never numeric-only, and `-N` is reserved solely for uniqueness. Existing non-overwrite behavior is unchanged.

### Filename-to-metadata round trip

For **newly generated** export files, the create response reason, the list response reason, the `latest_export` reason in `GET /api/exports/status`, and the visible UI reason must all resolve to the same canonical filename reason segment. The numeric uniqueness suffix must never become part of the reported reason.

The displayed reason is **filename-derived**. No database metadata table, sidecar metadata file, new API field, hidden persistent metadata, or frontend-side reconstruction of the slug is authorized. The frontend additionally maps a small set of known canonical slugs — `manual`, `before_import`, `before_update`, `before_large_edit`, `support_snapshot` — to Russian display labels, and renders any other canonical segment verbatim; that mapping is display-only.

### Legacy artifacts

This contract applies to newly generated artifacts only. Existing export files must not be renamed, rewritten, or deleted, and no database or filesystem migration is required or authorized.

Legacy artifact listing remains **best-effort**. Filename, path, created-timestamp fallback, size, and list availability must be preserved even when an old filename contains an ambiguous legacy reason. Exact round-trip recovery is **not** claimed for legacy ambiguous filenames. Legacy export manifests remain readable and are not rewritten.

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
