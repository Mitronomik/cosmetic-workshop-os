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
- Backup creation is implemented as a backend service operation that writes a transactionally consistent SQLite snapshot into `backups/` through the SQLite Online Backup API, without modifying the original database. See ADR 0015; the former raw file copy was removed by `CR-004`.
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

`CR-004` — the SQLite backup transaction-consistency question — is **resolved and accepted** (2026-08-02), classified `PRODUCT DEFECT — BACKUP CONSISTENCY`, severity `HIGH`. The raw `shutil.copy2` of the live main database file reproducibly omitted **all** committed-but-uncheckpointed WAL data while returning `quick_check = ok`, produced mixed transaction state including never-committed rows with the stock page cache, and in one scenario produced a structurally corrupt file. The source database was never mutated in any scenario. The accepted replacement is the SQLite Online Backup API with bounded busy behaviour. Full evidence and decision: `docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md` and `docs/backend-baseline-failure-triage.md` § 18. Nothing here implements or authorizes Restore.

## Accepted snapshot semantics (CR-004, decided 2026-08-02)

A successful SQLite backup is **one transactionally consistent snapshot of committed source-database state at one instant during the backup operation**. It contains only committed data, never part of one SQLite transaction, opens independently without the source WAL or rollback journal, and never modifies the source. It is **not** byte-identical to the source, and nothing may assert that it is.

A locked source fails the backup within one bounded wait (`5.0` seconds, the repository's existing SQLite connection timeout) rather than waiting indefinitely or producing a wrong file. `shutil.copy2` is not used for SQLite contents, and `-wal`, `-shm` and `-journal` files are never copied or guessed at.

## Canonical filename reason contract (CR-005, decided 2026-07-27)

`CR-005` is **accepted**. This section is the durable product contract for the backup filename reason segment. The contract itself is unchanged by any implementation slice.

**Implementation status: `DONE`.** `CR-005` remains **accepted**, and the correcting slice `R4 — Canonical backup/export filename reason normalization` is **merged and DONE** — PR #146, final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). **Merged `main` now implements the canonical reason contract described below.** New backup filenames use the shared helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the backup source database stem keeps its own separate sanitization and may still contain hyphens. Accepted merged backend result: `562 collected / 562 passed / 0 failed / 0 skipped`. The focused exact-head `/backups` and `/exports` browser smoke **passed** against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. The slice changed **no API response shape**, **no schema**, and involved **no database or filesystem migration**; **existing artifacts remain untouched** — none was renamed, rewritten, or deleted. `R4` changes neither the `CR-004` status above nor the Restore status: **`CR-004` remains unresolved** and **Restore remains unimplemented**. **Product release readiness is not claimed.** See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

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

## CR-009 manual-backup AuditLog boundary

`CR-009` accepts the durable artifact-primary and reconciliation semantics for
future manual-backup AuditLog coverage, but does not implement them here. A
fully written and verified manual backup remains available if AuditLog
finalization fails; the future create response remains HTTP `201` with
`audit_status: pending` and a separate Russian warning rather than a false
total failure. That future artifact-specific warning must name only the next
normal startup and the next manual-backup create as retry triggers; it must not
imply an immediate, periodic or background retry.

Runtime status:

```text
C3-II-B3 — IMPLEMENTED ON PR BRANCH — NOT MERGED
```

`CR-004` is resolved, so the accepted bounded ledger is now reused for manual
backups. `POST /api/backups` reserves the exact final filename, commits one
`prepared` ledger row, takes the snapshot, verifies the exact artifact and
finalizes exactly one `backup.created` AuditLog event. The create response is
built from the engine's exact `BackupResult` and no longer re-lists the backup
directory; `GET /api/backups/status` gains a read-only additive
`pending_audit_count`.

### The embedded prepared operation

Because the snapshot is taken **after** the prepared ledger row is committed, a
manual backup contains its own matching operation row in `status = prepared`
with `audit_log_id IS NULL`, and no `backup.created` event for itself. This is
intentional: a backup is a SQLite database, so unlike a document or an export it
can prove which operation produced it, and an unrelated but perfectly healthy
database placed at the same path cannot. `PRAGMA quick_check = ok` alone never
authorizes an audit event — an empty file returns `ok` too.

The completed backup is never rewritten afterwards to promote that row to
`audited`. A restored database therefore carries one unresolved `prepared`
operation, which normal post-migration startup reconciliation handles like any
other. Restore remains out of scope.

The future ledger `primary_filename` is an internal safe relative filename and
may contain the canonical filename-derived reason segment already accepted by
CR-005. The ledger has no separate reason column and stores no raw human or
request reason separately. The filename is never copied into AuditLog or
exposed by `GET /api/audit-logs`; CR-005 is not reopened.

Existing backup files are not backfilled, renamed, rewritten or audited
historically. The automatic `before_migration` startup backup is outside
CR-009: it is not a user action, remains before migrations, is not audited by
the CR-009 slices, and cannot depend on a ledger table that may not yet exist.
Full decision:
`docs/decisions/0013-file-backed-artifact-audit-semantics.md`.
