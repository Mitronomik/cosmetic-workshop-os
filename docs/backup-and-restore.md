# Backup and Restore

Default user data directory: `~/Documents/Мастерская косметолога/`.

Expected local user-data layout:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

Current foundation behavior:

- Development mode still uses repository-root `.local/cosmetic_workshop.sqlite` unless `COSMETIC_WORKSHOP_DB_PATH` is set.
- User-mode path resolution targets the default user data directory above, or `COSMETIC_WORKSHOP_USER_DATA_DIR` when explicitly overridden.
- Directory creation and database migration are explicit startup actions, not side effects of ordinary status/read endpoints.
- Backup creation is implemented as a backend service operation that copies an existing SQLite database file into `backups/` without modifying the original file.
- PR73 exposes a manual backup backend API: `GET /api/backups/status`, `GET /api/backups`, and `POST /api/backups`.
- Backup filenames include a UTC timestamp, the database filename stem, and a reason such as `before_migration`; if a generated filename already exists, the service chooses a non-overwriting suffixed filename.
- The `backups/` directory is part of the required user-data layout and may be created by explicit user-mode startup even when no backup file is created; a direct backup operation also creates it when needed.
- User-mode startup creates a `before_migration` backup only when the user database file already exists and pending migrations may be applied.
- Brand-new user-mode startup may create the empty `backups/` directory as part of the user-data layout, but it does not create a backup file for a database that does not exist yet.
- Ordinary status/settings reads and backup status/list reads must not create backup directories, backup files, databases, or migrations.
- Manual backup creation is explicit through `POST /api/backups`; it may create the selected backup directory and copies only the current configured SQLite database.
- Backup path selection keeps development backups next to the configured development database unless the database is the resolved user database path or `COSMETIC_WORKSHOP_USER_DATA_DIR` is explicitly set.
Current implementation status:

- the manual backup **UI is implemented** — `/backups` is a user-facing workspace that creates and lists local backups through the backup API;
- **local JSON exports are implemented**, together with their user-facing `/exports` workspace; see `docs/export.md`;
- **Restore is not implemented**;
- **scheduled backups are not implemented**;
- **CSV/XLSX export is not implemented**;
- **cloud backup is not implemented**.

`CR-004` — the potential SQLite backup transaction-consistency question — remains open and unresolved. Nothing in this document resolves it, and nothing here implements or authorizes Restore.

## Canonical filename reason contract (CR-005, decided 2026-07-27)

`CR-005` is **accepted**. This section is the durable product contract for the backup filename reason segment. The contract itself is unchanged by any implementation slice.

**Implementation status: `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE`.** The correcting slice `R4 — Canonical backup/export filename reason normalization` is implemented on branch `claude/r4-canonical-artifact-reason-normalization` and is **not merged**. On `main` the runtime still produces the older one-underscore-per-replaced-character output. New backup filenames on the `R4` branch use the shared helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the backup source database stem keeps its own separate sanitization and may still contain hyphens. `R4` changes neither the `CR-004` status above nor the Restore status. See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

### Two distinct reason representations

The product has two distinct representations, and they must not be silently conflated:

1. **Human reason** — the normalized user-supplied reason after the existing trim/default rule:

   ```text
   text = (reason or "manual").strip() or "manual"
   ```

2. **Filename reason segment** — a canonical, path-safe, unambiguous slug derived from the human reason.

### Canonical algorithm

For **newly created** backups, the filename reason segment is derived from the normalized human reason as follows:

1. preserve Unicode alphanumeric characters exactly;
2. treat underscore as a separator;
3. treat every non-alphanumeric character as a separator — whitespace, hyphen, dot, slash, backslash, punctuation, and symbols;
4. collapse every maximal run of separators into one underscore;
5. remove leading and trailing underscores;
6. when the result is empty, use `manual`;
7. when the result contains only digits, prefix it with `reason_` — for example `123` → `reason_123`;
8. preserve letter case;
9. preserve Unicode alphanumerics — no lowercasing and no transliteration;
10. no new length limit is introduced by this contract. The existing 80-character request-level limit on `reason` is unchanged.

The output therefore consists of alphanumeric groups separated by single underscores.

| Human reason | Canonical filename reason segment |
|---|---|
| `before/update ../unsafe` | `before_update_unsafe` |
| `before-import` | `before_import` |
| `___before---import___` | `before_import` |
| `перед обновлением` | `перед_обновлением` |
| `123` | `reason_123` |
| whitespace only | `manual` |
| punctuation only | `manual` |

### Hyphen decision

**Literal hyphens are not allowed inside a newly generated filename reason segment.** A hyphen normalizes to an underscore, because:

- the hyphen is already a structural separator in the backup filename grammar;
- backup metadata parsing splits the filename stem on `-`;
- allowing hyphens inside the reason makes the round trip ambiguous — a reason of `before-import` is currently recovered as `import`;
- the uniqueness suffix is also a hyphen followed by a number.

This decision applies **only** to the filename reason segment. It does not prohibit hyphens in the original human reason.

### Numeric-only decision

**A filename reason segment is never purely numeric.** A numeric-only human reason receives the `reason_` prefix, so that a reason such as `123` cannot be confused with the numeric uniqueness suffix `-1`, `-2`, `-3`.

This is not cosmetic. The metadata parser treats a trailing all-digit segment as a uniqueness suffix, so a numeric reason combined with a hyphenated source database stem — for example stem `my-db` and reason `123` — would otherwise be recovered as the stem fragment `db` rather than as the reason.

### Filename grammar

The existing grammar is preserved. No new filename version, marker, sidecar format, or migration is authorized. A new backup filename remains conceptually:

```text
{timestamp}-{safe_source_stem}-{canonical_reason}[-N].{sqlite_suffix}
```

where `canonical_reason` contains no hyphen and is never numeric-only, and `-N` is reserved solely for uniqueness. The source database stem keeps its own separate sanitization and may still contain hyphens. Existing non-overwrite behavior is unchanged.

### Filename-to-metadata round trip

For **newly generated** backup files, the create response reason, the list response reason, and the `latest_backup` reason in `GET /api/backups/status` must all be the same canonical filename reason segment. The visible UI reason must **resolve from** that same canonical segment — verbatim for an unmapped slug, or through the existing Russian display mapping for a known system slug, as described below.

- `before-import` → `before_import`
- `123` → `reason_123`

The uniqueness suffix must never become part of the reported reason: `...-before_import-2.sqlite` reports `before_import`.

### Displayed reason — canonical slug versus display label

The displayed reason is **filename-derived**, but the visible label is not always literally the canonical slug. The contract has two layers and both must be preserved:

1. **Backend/API `reason` is the canonical filename-derived slug.** It is the single source of truth. No database metadata table, sidecar metadata file, new API field, or hidden persistent metadata is authorized.
2. **The frontend receives that canonical slug from the API and must never reconstruct, sanitize, or normalize it.** It may only *present* it:
   - **known system slugs** are mapped to the **existing localized Russian display labels**;
   - **custom or unmapped canonical slugs are displayed verbatim.**

The current backup mapping in `frontend/src/main.ts` (`backupReasonLabelRaw`) is exactly:

| Canonical slug from the API | Visible label on `/backups` |
|---|---|
| `manual` | `Обычная резервная копия` |
| `before_import` | `Перед импортом` |
| `before_update` | `Перед обновлением приложения` |
| `before_large_edit` | `Перед крупными изменениями` |
| any other canonical slug | the canonical slug, verbatim |

So a backup created with the human reason `before-import` stores and reports the canonical slug `before_import` in the filename and in every API response, and the `/backups` screen shows the existing Russian label `Перед импортом` for it. A backup created with `before/update ../unsafe` reports the canonical slug `before_update_unsafe`, which is not in the mapping and is therefore shown verbatim as `before_update_unsafe`.

The label table above records existing frontend behavior. This decision does **not** introduce, remove, or reword any Russian label.

### Legacy artifacts

This contract applies to newly generated artifacts only. Existing backup files must not be renamed, rewritten, or deleted, and no database or filesystem migration is required or authorized.

Legacy artifact listing remains **best-effort**. Filename, path, created-timestamp fallback, size, and list availability must be preserved even when an old filename contains an ambiguous legacy reason. Exact round-trip recovery is **not** claimed for legacy ambiguous filenames, because the filename itself does not always contain enough information to recover the original reason.

### Out of scope for this contract

Report-document filenames and `sanitize_reason` in `backend/app/services/report_documents.py` are deliberately a **different** contract and are not covered here. Backup consistency semantics are unchanged by this decision, and `CR-004` — the potential SQLite backup transaction-consistency question — remains open and is **not** resolved by it.

Developer/test safety:

- Tests and smoke checks must use temporary directories, typically through `COSMETIC_WORKSHOP_USER_DATA_DIR` and/or `COSMETIC_WORKSHOP_DB_PATH`.
- Tests must not write to the real `~/Documents/Мастерская косметолога/` directory.
- Backup API tests must use temporary directories and environment overrides such as `COSMETIC_WORKSHOP_DB_PATH` and `COSMETIC_WORKSHOP_USER_DATA_DIR`.
