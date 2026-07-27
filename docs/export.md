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

`CR-005` is **accepted**. This section is the durable product contract for the export filename reason segment. The contract itself, including the rule that the export JSON manifest keeps the normalized **human** reason and that the export schema version is unchanged, is not altered by any implementation slice.

**Implementation status: `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE`.** The correcting slice `R4 — Canonical backup/export filename reason normalization` is implemented on branch `claude/r4-canonical-artifact-reason-normalization` and is **not merged**. On `main` the runtime still produces the older one-underscore-per-replaced-character output. New export filenames on the `R4` branch use the shared helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`, while `manifest.reason` continues to hold the normalized human reason. See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

### Human manifest reason versus canonical filename reason

Exports carry **two distinct** reason representations, and they must not be conflated:

| Representation | Where it appears | Value |
|---|---|---|
| **Human reason** | the export JSON manifest `reason` field | the normalized user-supplied reason — `text = (reason or "manual").strip() or "manual"` |
| **Canonical filename reason segment** | the filename, and the `reason` field of the create/list/status API responses | a canonical, path-safe, unambiguous slug derived from the human reason |

The **visible UI label** is a third, presentation-only layer derived from the canonical slug. It is not a separate stored value, and it is not always literally the slug — see *Displayed reason* below.

Worked example for the input `before-import`:

- filename reason segment: `before_import`
- API create/list/status `reason`: `before_import`
- export manifest `reason`: `before-import`
- visible UI label on `/exports`: `Перед импортом` — because `before_import` is a **known system slug** with an existing Russian display mapping

Worked example for the input `before-update ../unsafe`:

- filename reason segment: `before_update_unsafe`
- API create/list/status `reason`: `before_update_unsafe`
- export manifest `reason`: `before-update ../unsafe`
- visible UI label on `/exports`: `before_update_unsafe` — because the slug is **unmapped** and is therefore rendered verbatim

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

For **newly generated** export files, the create response reason, the list response reason, and the `latest_export` reason in `GET /api/exports/status` must all be the same canonical filename reason segment. The visible UI reason must **resolve from** that same canonical segment. The numeric uniqueness suffix must never become part of the reported reason.

### Displayed reason — canonical slug versus display label

The displayed reason is **filename-derived**, but the visible label is not always literally the canonical slug. Both layers must be preserved:

1. **Backend/API `reason` is the canonical filename-derived slug** and the single source of truth. No database metadata table, sidecar metadata file, new API field, or hidden persistent metadata is authorized.
2. **The frontend receives that canonical slug from the API and must never reconstruct, sanitize, or normalize it.** It may only *present* it:
   - **known system slugs** are mapped to the **existing localized Russian display labels**;
   - **custom or unmapped canonical slugs are displayed verbatim.**

The current export mapping in `frontend/src/main.ts` (`exportReasonLabelRaw`) is exactly:

| Canonical slug from the API | Visible label on `/exports` |
|---|---|
| `manual` | `Обычный экспорт` |
| `before_import` | `Перед импортом` |
| `before_update` | `Перед обновлением приложения` |
| `before_large_edit` | `Перед крупными изменениями` |
| `support_snapshot` | `Для поддержки` |
| any other canonical slug | the canonical slug, verbatim |

The export and backup mappings are separate and are **not** identical: `manual` renders as `Обычный экспорт` on `/exports` and as `Обычная резервная копия` on `/backups`, and `support_snapshot` exists only in the export mapping. The tables in this document and in `docs/backup-and-restore.md` record existing frontend behavior. This decision does **not** introduce, remove, or reword any Russian label.

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

The list above records the scope of **PR75 specifically** and is historical. Current implementation status: **local JSON exports and their user-facing `/exports` workspace are implemented**, as is the manual backup UI at `/backups`. Restore, scheduled exports, CSV/XLSX export, PDF export, download and delete endpoints, and cloud export remain **not implemented**.

## Testing

Automated tests use `tmp_path` and monkeypatch `COSMETIC_WORKSHOP_DB_PATH` and, where needed, `COSMETIC_WORKSHOP_USER_DATA_DIR`. Tests must not write to the real `~/Documents/Мастерская косметолога/` directory.
