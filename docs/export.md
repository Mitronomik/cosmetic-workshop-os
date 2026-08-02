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

**Implementation status: `DONE`.** `CR-005` remains **accepted**, and the correcting slice `R4 — Canonical backup/export filename reason normalization` is **merged and DONE** — PR #146, final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). **Merged `main` now implements the canonical reason contract described below.** New export filenames use the shared helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`, while `manifest.reason` continues to hold the normalized human reason and the export schema version is unchanged. Accepted merged backend result: `562 collected / 562 passed / 0 failed / 0 skipped`. The focused exact-head `/backups` and `/exports` browser smoke **passed** against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. The slice changed **no API response shape**, **no schema**, and involved **no database or filesystem migration**; **existing artifacts remain untouched** — none was renamed, rewritten, or deleted, and legacy manifests were not rewritten. **`CR-004` remains unresolved** and **Restore remains unimplemented**. **Product release readiness is not claimed.** See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

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

## Create-response confirmation contract (CR-006, decided 2026-08-01)

`CR-006` is **accepted**. The durable decision is
`docs/decisions/0014-json-export-create-confirmation-semantics.md`; this section
is the product-facing summary. It does **not** change `CR-005`, the manifest
reason, or the export schema version.

### What the diagnostic found

The current `POST /api/exports` re-scans the whole export directory after
`create_json_export` has already written and stat-ed the exact final file, then
falls back to `ExportResult` when that exact-path lookup fails. Executed
evidence against `1d4e90ccffb6f154882e685b09803f67f2f75ceb` shows:

- the fallback is **reachable in production-equivalent behavior**, not only
  through mocks — an ordinary per-file `stat` failure during the re-scan, or a
  directory-entry race between `iterdir()` and that `stat`, reaches it while the
  created export is present and correct on disk;
- when it runs, the response `reason` is the **human manifest reason**
  (`before-update ../unsafe`) instead of the canonical filename-derived slug
  (`before_update_unsafe`) that `CR-005` requires — and the frontend renders an
  unmapped API reason verbatim, so the wrong value would be visible on
  `/exports`;
- the same redundant re-scan can also turn a **fully successful** creation into
  a generic HTTP `500` when the listing raises;
- the re-scan can even match a **foreign** object that replaced the exact path
  after creation, and report its size as the created export's size.

Classification: **`PRODUCT DEFECT — CREATE-RESPONSE CONTRACT MISMATCH`**,
severity **`MEDIUM`**. No data loss, overwrite, incorrect export bytes, source
database mutation, or privacy exposure was found.

### The decided contract

1. **A successfully returned `ExportResult` is the authoritative result of the
   create operation.** The endpoint must not re-scan the export directory to
   decide whether the operation it just performed succeeded.
2. **The create response is built only from that exact result** — the exact
   final path and filename, the creator's timestamp, the creator's captured
   size, and the creator's entity counts.
3. **The API `reason` is the canonical reason parsed from the exact final
   filename**, through the same filename parsing contract list and status use.
   `ExportResult.reason` — the human manifest reason — must never be used as the
   API reason.
4. **`list_export_files` stays authoritative for the independent `GET` reads.**
   It is not the confirmation mechanism for a `POST` that already returned an
   exact result, and the `GET` contract is unchanged.
5. **External disappearance does not retroactively falsify creation.** `201
   Created` means the application completed creation at the operation boundary;
   it does not promise that no external process ever removes or replaces the
   file afterwards. The `GET` endpoints remain the truthful current-state
   surface, and externally substituted content is never the
   application-created artifact.
6. **A creator that does not return successfully must never be reported as
   success.** Post-write failures before a successful return keep their own
   explicit error contract and are governed by the future `C3-II-B2`
   verification and reconciliation contract.

### What this decision does not change

The manifest keeps the normalized human reason; the export schema version is
unchanged; no sidecar, metadata table, second persisted reason, or new reason
field is introduced; existing exports are never renamed or rewritten; and
`CR-005` is not reopened. **No production code is changed by the decision
itself** — the correction is carried by `C3-II-B2`, which is implemented on
branch `claude/c3-ii-b2-json-export-audit` and **not merged**.

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

## CR-009 JSON-export AuditLog coverage

`CR-009` accepts the durable artifact-primary and reconciliation semantics for
JSON-export AuditLog coverage. A fully written and verified export remains
available if AuditLog finalization fails; the create response remains HTTP `201`
with `audit_status: pending` and a separate Russian warning rather than a false
total failure. That artifact-specific warning names only the next normal startup
and the next JSON-export create as retry triggers; it does not imply an
immediate, periodic or background retry.

Runtime status:

```text
C3-II-B2 — IMPLEMENTED ON PR BRANCH — NOT MERGED
```

`CR-006` is resolved and accepted
(`docs/decisions/0014-json-export-create-confirmation-semantics.md`), so the
accepted bounded ledger is reused for JSON exports. `C3-II-B2` is **one bounded
implementation pull request**, implemented on branch
`claude/c3-ii-b2-json-export-audit` and **not merged**. It also carries the
accepted `CR-006` create-response correction, so the export create path is
touched exactly once. Its full scope, export verification contract and non-goals
are in `docs/implementation-plan.md` § *C3-II-B2 — JSON export AuditLog
coverage*. `C3-II-B3` remains blocked by `CR-004`.

### What the branch implements

- **The `CR-006` correction.** `POST /api/exports` no longer calls
  `list_export_files`. The response is built from the exact `ExportResult`, and
  `reason` comes from the exact final filename through `parse_export_reason` —
  the same function list and status use. `ExportResult.reason` is never the API
  reason.
- **One filename-selection algorithm.** `reserve_export_path` chooses the exact
  final path once; `create_json_export` accepts it as a strictly validated
  `reserved_export_path` and writes to that path and no other. An active ledger
  identity counts as occupied alongside an existing file, so the `-N` uniqueness
  suffix advances past both.
- **Ledger preparation before the write.** One `prepared` row in the existing
  `artifact_audit_operations` table — `artifact_kind = json_export`,
  `audit_action = export.created`, `primary_filename` = the exact safe final
  filename, `companion_filename = null`, because an export is one file. **No new
  migration**; `0020` is reused unchanged.
- **Exact-path verification.** The verifier inspects only the exact ledger-named
  file: safe name, resolution inside the export directory, escaping symlinks
  refused, existence, regular file, the **complete** filename grammar, JSON
  parses, top-level keys exactly `manifest` and `data`, supported
  `export_schema_version`, `source == "cosmetic-workshop-os"`, a **human**
  `manifest.reason` that is not required to equal the canonical slug, and
  manifest table counts that agree with the exported data. It never rewrites the
  export and never compares historical exported data with the current database.
- **The filename grammar is checked by round trip, not by resemblance.**
  `parse_generated_export_filename` validates the complete timestamp, extracts
  the canonical reason and the optional numeric uniqueness suffix, requires the
  reason to satisfy `normalize_artifact_reason_segment(reason) == reason` and to
  not be digits-only, and then rebuilds the name through `_export_filename` —
  the one generation algorithm — and requires byte-for-byte equality. Both the
  writer's `reserved_export_path` check and the ledger verifier use it, so a
  name this application could not have generated can be neither reserved nor
  audited, however valid its JSON contents are. `list_export_files` deliberately
  does **not** use it: the independent `GET` listing stays best-effort so legacy
  exports keep appearing in the user's history, exactly as CR-005 accepted.
- **Exactly-once finalization.** One `BEGIN IMMEDIATE` transaction on one
  connection commits the `export.created` AuditLog row together with the
  `audited` ledger transition, or commits neither.
- **Reconciliation** at normal startup after migrations, and once before the
  next JSON-export create. No background worker, timer or unbounded retry.

Create response, implemented on that branch:

```json
{
  "message": "Экспорт создан.",
  "audit_status": "recorded",
  "audit_message": null
}
```

```json
{
  "message": "Экспорт создан.",
  "audit_status": "pending",
  "audit_message": "Экспорт создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта."
}
```

### Verification failure is not a pending Journal entry

*C3 artifact-finalization hardening — implemented on the PR branch, not merged.*

Finalization reports three distinct outcomes — `recorded`, `audit_pending` and
`artifact_invalid` — instead of an ID-or-nothing. Only the first two make the
export authoritative.

`artifact_invalid` means mandatory verification did not conclude the export is
valid: an `ambiguous` verdict, `definitely_absent` on the immediate create path,
a verifier that raised, or a ledger that could not be read. In that case the
create does **not** return `201`, does **not** say `Экспорт создан.`, writes no
`export.created` event, and is never described as merely awaiting a Journal
entry. It returns HTTP `500` with the fixed structured detail
`export_verification_failed` and no filename, path, human or canonical reason,
operation ID, schema version, entity count, verifier reason or SQLite message.

The file is left on disk untouched — the create cannot prove it owns that path,
which is exactly what verification failed to establish — and its operation stays
unresolved and counted, so a later bounded reconciliation pass finalizes it
exactly once if the artifact turns out to be valid.

`audit_pending` is unchanged and remains a success: the export is verified and
authoritative, and only its Journal entry is outstanding. `CR-006` is untouched:
a successful response is still built from the exact `ExportResult`, never from a
re-read of the export directory.

Every existing export metadata field stays present, and the response `reason`
stays the canonical final-filename-derived reason. In the pending case the
export remains available, listable and byte-identical, and the user must **not**
repeat the create request. `GET /api/exports/status` additionally gains
`pending_audit_count`, counting exactly the ledger rows with
`artifact_kind = json_export` and `status IN (prepared, pending_audit)`; that
GET stays read-only, performs no reconciliation, and raises a safe HTTP `500`
rather than reporting a fabricated `0` when the ledger cannot be read.

The adjacent post-write `stat` failure recorded as ADR 0014 § 8.8 is covered:
the export stays on disk, its committed `prepared` row stays unresolved, no
success event is written during the failed request, and a later startup or
pre-create reconciliation verifies the exact reserved file and finalizes it
exactly once.

The ledger `primary_filename` is an internal safe relative filename and
may contain the canonical filename-derived reason segment already accepted by
CR-005. The ledger has no separate reason column and stores no raw human
reason, request reason or export-manifest reason separately. The filename is
never copied into AuditLog or exposed by `GET /api/audit-logs`; CR-005 is not
reopened.

Existing export files and manifests are not backfilled, renamed, rewritten or
audited historically. AuditLog must never store an export path, filename,
reason, contents, database contents, entity counts, request/response payload or
arbitrary user text. Full decision:
`docs/decisions/0013-file-backed-artifact-audit-semantics.md`.
