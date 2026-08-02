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
- **Restore is not implemented.** Its product contract is **decided** — `CR-010`, launcher-assisted, see § *Accepted Restore contract (CR-010)* below. The internal launcher-owned safety engine `C4-I` is **implemented on a pull-request branch and not merged**; it has no user-facing entry point, so product Restore remains `NOT IMPLEMENTED`. See § *C4-I implementation* at the end of this document;
- **scheduled backups are not implemented**;
- **CSV/XLSX export is not implemented**;
- **cloud backup is not implemented**.

`CR-004` — the SQLite backup transaction-consistency question — is **resolved and accepted** (2026-08-02), classified `PRODUCT DEFECT — BACKUP CONSISTENCY`, severity `HIGH`. The raw `shutil.copy2` of the live main database file reproducibly omitted **all** committed-but-uncheckpointed WAL data while returning `quick_check = ok`, produced mixed transaction state including never-committed rows with the stock page cache, and in one scenario produced a structurally corrupt file. The source database was never mutated in any scenario. The accepted replacement is the SQLite Online Backup API with bounded busy behaviour. Full evidence and decision: `docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md` and `docs/backend-baseline-failure-triage.md` § 18. That decision implements and authorizes no Restore behaviour; the Restore **product contract** is decided separately by `CR-010` below and is likewise not implemented.

## Accepted snapshot semantics (CR-004, decided 2026-08-02)

A successful SQLite backup is **one transactionally consistent snapshot of committed source-database state at one instant during the backup operation**. It contains only committed data, never part of one SQLite transaction, opens independently without the source WAL or rollback journal, and never modifies the source. It is **not** byte-identical to the source, and nothing may assert that it is.

A locked source fails the backup within one bounded wait (`5.0` seconds, the repository's existing SQLite connection timeout) rather than waiting indefinitely or producing a wrong file. `shutil.copy2` is not used for SQLite contents, and `-wal`, `-shm` and `-journal` files are never copied or guessed at.

## Canonical filename reason contract (CR-005, decided 2026-07-27)

`CR-005` is **accepted**. This section is the durable product contract for the backup filename reason segment. The contract itself is unchanged by any implementation slice.

**Implementation status: `DONE`.** `CR-005` remains **accepted**, and the correcting slice `R4 — Canonical backup/export filename reason normalization` is **merged and DONE** — PR #146, final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). **Merged `main` now implements the canonical reason contract described below.** New backup filenames use the shared helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the backup source database stem keeps its own separate sanitization and may still contain hyphens. Accepted merged backend result: `562 collected / 562 passed / 0 failed / 0 skipped`. The focused exact-head `/backups` and `/exports` browser smoke **passed** against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. The slice changed **no API response shape**, **no schema**, and involved **no database or filesystem migration**; **existing artifacts remain untouched** — none was renamed, rewritten, or deleted. `R4` changed neither the `CR-004` status nor the Restore status. `CR-004` was resolved separately and is now **accepted and implemented** (see above), and **Restore remains unimplemented**. **Product release readiness is not claimed.** See `docs/implementation-plan.md` and `docs/backend-baseline-failure-triage.md`.

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

Report-document filenames and `sanitize_reason` in `backend/app/services/report_documents.py` are deliberately a **different** contract and are not covered here. Backup consistency semantics are unchanged by the `CR-005` decision; the SQLite backup transaction-consistency question was resolved separately as `CR-004` and is recorded above.

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
C3-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
```

`C3-II-B3` merged as PR #167 — final reviewed head
`259697805660fd4dc37e6ac5f50567d48037be94`, merge commit
`7af53a3305fa9fdb984d4c478e1186685fbb6727`. The C3 artifact-finalization
hardening then merged as PR #168 — final reviewed head
`6c57c7f5ba851ce2124577268baeda07d19ce4ae`, merge commit
`867afeb0967637d07172f88c95e02e9bc500a311`, merged `2026-08-02T08:34:02Z` — so
`C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED`.

`CR-004` is resolved, so the accepted bounded ledger is now reused for manual
backups. `POST /api/backups` reserves the exact final filename, commits one
`prepared` ledger row, takes the snapshot, verifies the exact artifact and
finalizes exactly one `backup.created` AuditLog event. The create response is
built from the engine's exact `BackupResult` and no longer re-lists the backup
directory; `GET /api/backups/status` gains a read-only additive
`pending_audit_count`.

### Verification failure is not a pending Journal entry

Only a fully written **and successfully verified** backup is an authoritative
result eligible for `201`. If verification does not conclude that the artifact is
valid, the create returns one fixed safe Russian error instead: it does not
report a created backup, does not write a `backup.created` event, and does not
present the problem as a merely pending Journal entry.

The artifact is left where it is — this operation cannot prove it owns that path,
which is precisely what verification failed to establish — and the ledger row
stays unresolved and counted for diagnosis and bounded reconciliation.

### Destination ownership and the commit point

The snapshot is written into an exclusively created scratch file and then
published onto the reserved name with no-replace semantics. An existence check
followed by an open is not an ownership guarantee, because another process can
create the destination in between. No foreign file is ever overwritten, and
failure cleanup only ever removes the engine's own scratch file.

**Publication is the artifact commit point.** All fallible engine-owned size
collection happens before it, so once a backup is published no filesystem
metadata failure can turn it into a reported failure. After publication,
mandatory verification decides whether the artifact is authoritative, and
AuditLog persistence is a separate secondary result.

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
other. Restore is out of scope for `CR-009`; its own contract is `CR-010` below.

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

---

# Accepted Restore contract (CR-010, decided 2026-08-02)

```text
Restore — NOT IMPLEMENTED
CR-010 — ACCEPTED
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4-II — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
```

This section is the durable product contract for Restore. It describes decided
behaviour. The internal safety engine of § 14 `C4-I` now exists on an unmerged
pull-request branch; **no user-facing Restore behaviour is shipped**, and product
Restore stays `NOT IMPLEMENTED` until `C4-II` and `C4-III` are authorized,
implemented and merged. The rationale, rejected alternatives and consequences are
in `docs/decisions/0016-launcher-assisted-restore.md`.

## The decision

```text
MVP Restore is launcher-assisted.

Restore is not performed by a running FastAPI backend endpoint and is not
implemented as an ordinary SPA mutation.

The launcher owns process shutdown, backup validation, the pre-restore safety
copy, staging, atomic database replacement, post-restore startup verification,
rollback, and incomplete-restore recovery.
```

Support-assisted recovery remains a **fallback** for failures that cannot be
resolved automatically. It is not the primary MVP Restore workflow.

The user must never need Git, Python, Node.js, Docker, SQLite tools, GitHub or a
terminal in order to restore a backup.

## 1. Restore source

Restore accepts a locally selected SQLite backup that passes the
application-owned validation contract below. The selected source may be:

- a current manual backup produced by the application;
- a historical application backup from a supported schema version;
- a backup copied to another local directory or external drive.

**The backup filename is not sufficient proof that the file is valid.**

Restoring the following is not authorized:

- JSON exports;
- CSV or XLSX files;
- report documents;
- arbitrary unknown SQLite databases;
- a directory;
- a symbolic link;
- a cloud URL;
- a network service;
- a partial set of tables.

**Restore is whole-database only.** There is no partial-table import, no merge
and no selective record recovery.

The selected source file is **read-only input** and must never be modified,
renamed, migrated, deleted or rewritten — including on the failure and rollback
paths. After a successful Restore it must remain byte-identical.

## 2. Process ownership

Restore runs while the normal application backend is **stopped**. The launcher
must:

1. prevent a second application instance from starting;
2. stop the current backend cleanly when it is running;
3. confirm that the database is no longer in active application use;
4. perform Restore outside the ordinary API process;
5. start the backend only after the restore transaction reaches the verification
   stage;
6. open the ordinary browser UI only after Restore succeeds completely.

Not authorized: replacing the database from a running FastAPI request; frontend
coordination as the locking mechanism; a hidden terminal command as the user
workflow; direct database replacement while Uvicorn still has the database open.

## 3. Backup validation

```text
The staged candidate must pass the complete Restore validation contract
before any mutation, replacement, deletion or migration of the current
working database.
```

The selected backup is validated from a **staged read-only copy**. Staging is
Restore infrastructure, not a mutation of the business workspace:

```text
Before candidate validation completes, the launcher may create only:
- the isolated launcher-owned restore-operation directory;
- the narrow durable operation record;
- launcher-owned staging files inside that directory;
- local technical logs that follow the accepted privacy contract.

Those writes are Restore infrastructure and do not mutate the current
working database or business data.
```

The user-selected source remains immutable throughout.

Validation must include at least:

- the selected path resolves to a regular local file;
- no symlink or path-escape behaviour;
- SQLite can open the staged copy read-only;
- the file is not empty;
- structural checks succeed;
- the application migration-history table exists;
- migration IDs form a known, ordered prefix of the current application
  migration chain;
- there are no unknown, duplicated, reordered or skipped migration IDs;
- the backup is not from a schema newer than the running application;
- required application tables for the recorded schema level exist;
- the database is recognizably a `cosmetic-workshop-os` workspace rather than an
  arbitrary SQLite file;
- the candidate does not depend on an external `-wal`, `-shm` or
  rollback-journal file;
- validation performs no business-data mutation;
- validation does not silently repair the backup.

**`PRAGMA quick_check = ok` alone must not be treated as sufficient proof** — the
`CR-004` evidence above shows empty files, WAL-era copies missing every committed
row and mixed-transaction copies all returning `ok`.

A backup from a **newer unsupported schema is rejected before the current
database changes**. An **older but known and migratable schema may be accepted**;
the candidate itself stays immutable, and normal application migrations operate
only on the restored working copy after replacement.

## 4. Explicit confirmation

```text
select backup
→ validate and show human-readable backup information
→ explicit destructive confirmation
→ execute Restore
```

The confirmation screen must clearly state which backup was selected; when it was
created, when that can be established safely; that current workshop data will be
replaced; that a safety copy of the current database will be created first; that
the selected backup will remain unchanged; that the application will restart; and
that the operation must not be interrupted.

**Validation failure must never show the destructive confirmation action as
available.** Raw SQL, migration IDs, internal paths, stack traces and SQLite
messages must not appear in the ordinary user-facing result.

## 5. Mandatory pre-restore safety copy

Before replacing the current database, the launcher creates a transactionally
consistent safety copy of the current database using the already accepted safe
SQLite backup engine (ADR 0015). `shutil.copy2` must not be reintroduced for
SQLite contents.

The safety backup reason is the existing canonical system reason:

```text
before_restore
```

The safety copy must complete and pass verification **before** database
replacement; must remain available after a successful Restore; must not be
silently deleted; is a system recovery artifact rather than the selected Restore
source; must not require a new generic backup service; and must not create a
false success if its creation or verification fails.

If the current database exists and the safety copy cannot be created and
verified, **Restore stops before replacing anything**, and the selected source
backup remains unchanged. The safety copy is not optional.

## 6. Staging and atomic replacement

The working database is never replaced directly from the user-selected path.

```text
validate request and source path
→ create an isolated restore-operation directory        [phase prepared]
→ copy the selected source into a launcher-owned
  staging file                                          [phase source_staged]
→ validate the staged candidate                         [phase candidate_validated]
→ create and verify the pre-restore safety copy         [phase safety_copy_verified]
→ durably persist the replacement intent                [phase replacement_intent]
→ atomically replace the working database from a file
  staged in the same filesystem/directory boundary
→ durably persist that the boundary completed           [phase replacement_committed]
→ durably persist that verification is starting         [phase verification_in_progress]
→ start the application against the exact restored database path
→ run migrations when required
→ verify startup and basic reads
→ durably persist completion                            [phase completed]
→ open the ordinary browser
→ clean only launcher-owned temporary staging files
```

The replacement mechanism must not silently overwrite an unrelated foreign file.
The implementation may use a same-directory atomic replacement primitive, but it
must be proved by tests and isolated smoke.

**Filesystem replacement and SQLite are not one database transaction, and no
document may claim they are.** That gap is exactly why the durable phase machine
of § 7 is mandatory.

## 7. Durable Restore operation state

Exactly one narrowly scoped, launcher-owned Restore operation record is
authorized, stored **outside the working database**. It is not a generic workflow
engine, job queue, outbox, cloud state store or application-wide transaction
framework, and it is not a business-domain entity.

It may contain only the minimum required for deterministic recovery: a
launcher-generated operation ID; safe relative launcher-owned filenames; **the
authoritative `phase`**; timestamps.

It must not persist database contents, client information, arbitrary
user-authored text, credentials, raw absolute source paths when a staged relative
identity is sufficient, or SQL errors and stack traces.

**`phase` is the sole authoritative lifecycle field, and it is mutually
exclusive.** Facts such as *whether database replacement occurred* and *whether
rollback completed* are **derived from `phase`** and must never be persisted as
independent authoritative fields that could contradict it.

The complete authoritative definitions, transition graph, persistence ordering
and rationale live in `docs/decisions/0016-launcher-assisted-restore.md` § 7. The
vocabulary, transitions and recovery matrix below are the operational contract
and must stay synchronized with that ADR; where they ever disagree, the ADR
governs.

### 7.1. Phase vocabulary

Exactly twelve phases exist, as internal lowercase-ASCII machine values. No
alias, no prose-only synonym and no additional phase is authorized.

```text
prepared
source_staged
candidate_validated
safety_copy_verified
replacement_intent
replacement_committed
verification_in_progress
completed
aborted
rollback_in_progress
rolled_back
recovery_blocked
```

| Phase | Meaning |
|---|---|
| `prepared` | Operation ID generated, isolated operation directory created, initial record durably written. No complete staged candidate yet; the working database is unchanged. |
| `source_staged` | The launcher-owned staged candidate is copied and durably published inside the operation directory. Source and working database unchanged; the candidate has not yet passed validation. |
| `candidate_validated` | The staged candidate passed the complete validation contract of § 3. The working database remains unchanged. |
| `safety_copy_verified` | The mandatory pre-restore safety gate completed: a transactionally consistent safety copy exists and passed verification. The working database has not entered the replacement boundary. |
| `replacement_intent` | Durably persisted immediately **before** the atomic replacement boundary. Replacement may not yet have happened, may be in progress, or may already have happened — a deliberately ambiguous crash window. |
| `replacement_committed` | The atomic replacement call returned successfully and that fact was durably recorded. The restored database is still unverified and not authoritative; the browser stays blocked. |
| `verification_in_progress` | Durably recorded **before** starting the backend, migrations or post-restore verification. The restored database is provisional; any crash or failure here requires rollback. |
| `completed` | All accepted post-restore checks passed and completion was durably recorded. **Only this phase makes the restored database authoritative, and the browser may open only after it.** |
| `aborted` | The operation ended **before** `replacement_intent`. The working database was never replaced and remains authoritative. Only launcher-owned staging may be cleaned; an existing verified safety copy is not silently deleted. **Terminal, non-destructive.** |
| `rollback_in_progress` | Rollback durably requested **before** entering the rollback replacement boundary. Must be idempotent or safely repeatable after a crash. Backend and browser remain blocked. |
| `rolled_back` | The safety copy was restored to the exact working database path and passed rollback verification. **Restore failed**; the previous workspace is authoritative again. **Terminal failed-Restore**, never success. |
| `recovery_blocked` | The launcher cannot prove the working database or rollback result is safe. Nothing starts, all evidence is preserved, and only a fixed non-technical support-assisted result is shown. **Terminal for automatic recovery.** |

If the application does not support Restore without an existing working
database, that case is rejected **before** `safety_copy_verified` rather than
silently weakening the safety-copy requirement.

### 7.2. Transition overview

Normal path:

```text
prepared
→ source_staged
→ candidate_validated
→ safety_copy_verified
→ replacement_intent
→ replacement_committed
→ verification_in_progress
→ completed
```

Failure before the replacement boundary:

```text
prepared → aborted
source_staged → aborted
candidate_validated → aborted
safety_copy_verified → aborted
```

Rollback:

```text
replacement_intent → rollback_in_progress
replacement_committed → rollback_in_progress
verification_in_progress → rollback_in_progress
rollback_in_progress → rolled_back
rollback_in_progress → recovery_blocked
```

Terminal phases: `completed`, `aborted`, `rolled_back`, `recovery_blocked`.

**No other transition is authorized.** In particular these are prohibited:

```text
replacement_intent → completed
replacement_committed → completed
verification_in_progress → ordinary startup without completed
rollback_in_progress → completed
rolled_back → completed
recovery_blocked → ordinary startup
aborted → replacement_intent
```

A new Restore attempt is a new operation with a new operation ID; a terminal
operation record is never reactivated.

### 7.3. Crash-safe persistence ordering

Every phase transition is persisted through one documented and tested crash-safe
launcher-owned write boundary **before** the launcher begins the next action
whose recovery behaviour depends on that phase. **An in-place
truncate-and-rewrite of the only operation record is not sufficient.** The
primitive chosen in `C4-I` must give a complete old record or a complete new
record after interruption, never a partially written authoritative record, with
an atomic publication boundary, documented file and parent-directory durability
handling, and tests injecting faults at every publication boundary. No document
may claim stronger durability than the chosen platform primitive can prove.

Destructive ordering: durably record `replacement_intent` → enter the atomic
replacement boundary → on success durably record `replacement_committed` →
durably record `verification_in_progress` → start backend, migrations and
post-restore checks → durably record `completed` only after all pass → open the
browser only after durable `completed`.

Rollback ordering: stop any partially started backend → durably record
`rollback_in_progress` → enter the rollback replacement boundary → verify the
restored previous workspace → durably record `rolled_back` → only then permit
ordinary startup of the recovered workspace.

If a required transition cannot be durably persisted, the launcher must not
continue to the next destructive step. Any failure after replacement and before
`completed` must enter or recover through rollback.

**The `replacement_intent` crash rule is mandatory:**

```text
A persisted replacement_intent is treated as though replacement may have
occurred, even when the current working file appears unchanged.
```

The launcher must not resolve that ambiguity from modification timestamps, file
size alone, filenames, inode identity alone, migration version alone, or the
apparent business contents of the working database. The safe outcome is rollback
from the verified safety copy.

### 7.4. Startup recovery matrix

An incomplete Restore operation is detected and resolved **before the normal
backend starts**. Every persisted phase has exactly one required startup
behaviour. **An interrupted Restore may never be ignored.**

| Persisted phase | Working-database authority | Required startup behaviour |
|---|---|---|
| `prepared` | Existing working database | Do not replace or roll back. Mark or recover the operation as `aborted`; clean only verified launcher-owned temporary files; then use normal startup. |
| `source_staged` | Existing working database | Do not replace or roll back. Treat the staged candidate as incomplete for execution; transition to `aborted`; preserve the selected source; clean only owned staging; then use normal startup. |
| `candidate_validated` | Existing working database | Do not replace or roll back. Transition to `aborted`; do not execute replacement automatically; then use normal startup. |
| `safety_copy_verified` | Existing working database | Replacement was not authorized yet. Do not infer replacement. Transition to `aborted`; retain the verified safety copy; then use normal startup. |
| `replacement_intent` | Ambiguous — replacement may or may not have occurred | Block ordinary startup. Durably enter `rollback_in_progress`; restore the verified safety copy; verify it; then record `rolled_back`, otherwise `recovery_blocked`. |
| `replacement_committed` | Restored database is provisional and unverified | Block ordinary startup. Durably enter `rollback_in_progress`; restore and verify the safety copy; record `rolled_back`, otherwise `recovery_blocked`. |
| `verification_in_progress` | Restored database is provisional and unverified | Stop any partial backend. Block ordinary startup. Durably enter `rollback_in_progress`; restore and verify the safety copy; record `rolled_back`, otherwise `recovery_blocked`. |
| `completed` | Restored working database | Do not roll back. Confirm the completed record is readable, retain the safety copy, clean only verified launcher-owned temporary staging, and continue normal startup against the exact restored path. |
| `aborted` | Existing working database | Do not replace or roll back. Clean only verified launcher-owned temporary staging and continue normal startup. |
| `rollback_in_progress` | No working database may be trusted yet | Block ordinary startup. Continue or safely repeat rollback from the verified safety copy. Record `rolled_back` only after verification; otherwise record `recovery_blocked`. |
| `rolled_back` | Recovered previous working database | Confirm rollback verification and continue against the recovered previous workspace. Restore remains failed. Future UI must report that the previous workspace was recovered. |
| `recovery_blocked` | None | Do not start the ordinary backend or browser. Preserve all recovery evidence and expose only the fixed support-assisted recovery result. |

`C4-I` implements this matrix exactly. It is the accepted MVP recovery
behaviour, not a default an implementation may replace with an equivalent of its
own choosing.

## 8. Schema migration boundary

Restore and migration are distinct responsibilities. The launcher restores a
validated working copy; the normal startup migration system may then migrate an
older supported restored schema. Existing invariants remain mandatory: a backup
must exist before migration; migrations are ordered; migrations must not silently
mutate historical business meaning; migration failure must not produce a false
successful Restore; a newer-than-current schema is rejected before replacement.

No second migration framework is authorized for Restore, and the selected source
backup is never migrated.

## 9. Post-restore verification

Restore is successful only after all required verification passes:

- the backend starts successfully;
- the backend and launcher use the exact same restored database path;
- migrations completed when required;
- the database can be opened normally;
- application health succeeds;
- a bounded set of representative read-only application endpoints succeeds;
- no unexpected fallback database was created;
- the ordinary application can be restarted against the restored data;
- the selected source backup remains byte-identical;
- the pre-restore safety backup remains available.

These checks run under phase `verification_in_progress` and may use the existing
backend health and read-only endpoints. Passing them all is what authorizes the
durable transition to `completed`.

**The browser UI is not opened into the normal workspace until `completed` has
been durably recorded.**

## 10. Rollback

If any failure occurs after database replacement but before successful
completion, the launcher must:

1. stop the partially started backend;
2. preserve diagnostic evidence without exposing it to the user;
3. durably record `rollback_in_progress`;
4. restore the pre-restore safety copy through the same launcher-owned safe
   replacement boundary;
5. verify the rolled-back database can start;
6. durably record `rolled_back`, or `recovery_blocked` when the rollback result
   cannot be proved safe;
7. report that Restore did not complete and that the previous workspace was
   recovered.

Rollback is not optional, and it is entered from `replacement_intent`,
`replacement_committed` or `verification_in_progress` only. If rollback
succeeds, the user must not be told that Restore succeeded — `rolled_back` is a
failed Restore. If rollback fails, the product must not continue with an
uncertain database; it enters `recovery_blocked` and stops.

## 11. AuditLog boundary

**No Restore AuditLog event is authorized**, and `restore.completed` is **not**
implicitly authorized. A Restore AuditLog event requires a separately explicit C4
decision, because the database containing the event is itself being replaced and
migrated. No event may be written into the database being discarded, and
filesystem operation-state evidence is not AuditLog. See `docs/audit-log.md`.

## 12. User data and privacy

No backup contents, database contents, client data, recipe data, contact data or
workshop profile data may be uploaded anywhere. No network connection is required
for Restore. User-visible errors are fixed, human-readable and non-technical, and
technical detail belongs only in local logs.

## 13. Backend and frontend boundaries

Backend: no ordinary FastAPI Restore mutation endpoint; the backend is stopped
during replacement; normal backend startup and migration services remain
authoritative after replacement; post-restore verification may use existing
health and read endpoints; no business repository writes are authorized as part
of validation; no new Restore AuditLog event; no new migration.

Frontend: ordinary SPA routes do not own database replacement; the final
user-facing Restore flow belongs to the launcher/application shell; the SPA must
not attempt to coordinate a restore lock; the frontend must not parse SQLite,
migrations, database paths or backup contents; `C4-II` will later define the
user-facing launcher flow; no Restore route, button, dialog or API call is
authorized.

## 14. C4 subdivision

### C4-I — Launcher-owned restore safety engine

```text
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
```

The only runtime slice authorized by `CR-010`. Scope: launcher-owned
restore operation domain vocabulary; source and staged-candidate validation;
schema-lineage compatibility validation; pre-restore safety-copy orchestration
using the existing safe backup engine; isolated restore operation directory; **the
exact twelve-phase durable operation state of § 7.1 with `phase` as the sole
authoritative lifecycle field**; **the exact transition graph of § 7.2**; **the
crash-safe persistence ordering of § 7.3, with a publication boundary proved by
fault-injection tests**; same-filesystem staging; atomic working-database
replacement preceded by durable `replacement_intent`; automatic rollback through
`rollback_in_progress`; **the complete startup recovery matrix of § 7.4**,
resolved before backend startup; backend/database-path continuity; backend
startup and bounded health verification; focused backend/launcher tests; isolated
exact-head launcher smoke.

`C4-I` implements the accepted state machine **exactly**. It must not rename
phases; omit `replacement_intent`; infer replacement from filesystem appearance;
start the ordinary backend from an unsafe phase; expose the ordinary browser
before durable `completed`; treat `rolled_back` as successful Restore; recover
`recovery_blocked` automatically by guessing; use independent contradictory
replacement/rollback booleans; or use an in-place rewrite as the sole
authoritative operation-state persistence mechanism. Any proposed deviation
requires a new explicit documentation decision before runtime implementation.

`C4-I` must not expose a final user-facing Restore entry point yet and must
provide no terminal workflow to the product user. It must not modify frontend
production code unless repository evidence proves a minimal shared contract
module is unavoidable, documented before implementation rather than assumed.

### C4-II — User-facing launcher Restore flow

```text
PLANNED — NOT AUTHORIZED
```

Reserved: file selection; validation progress; human-readable backup summary;
explicit destructive confirmation; progress and restart states; successful
completion screen; rollback-completed screen; support-assisted failure screen;
keyboard and accessibility behaviour; narrow-viewport behaviour where
applicable; no terminal requirement.

### C4-III — Restore end-to-end verification and lifecycle closure

```text
PLANNED — NOT AUTHORIZED
```

Reserved: complete exact-package Restore smoke; older supported schema Restore;
current schema Restore; corrupt/foreign/newer-schema rejection; interruption
recovery; post-replacement startup failure and rollback; repeated launch after
successful Restore; selected source immutability; safety-copy retention; C4
lifecycle closure.

## 15. Lifecycle

```text
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4 — ACTIVE
C4 product decision — COMPLETE
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
C4-II — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

`CR-010` reopens none of `CR-004`, `CR-005`, `CR-006`, `CR-007`, `CR-008` or
`CR-009`.

---

# 16. C4-I implementation — the launcher-owned safety engine

```text
C4-I — IMPLEMENTED ON PR BRANCH — NOT MERGED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

This section records **exactly what the branch implements**. It adds no decision:
every rule above still governs, and `C4-I` implements the accepted state machine
of § 7 without renaming a phase, omitting `replacement_intent` or substituting an
equivalent of its own.

There is **no** Restore API endpoint, button, dialog, file picker, frontend route
or product terminal workflow. The engine is internal Python called by a future
`C4-II`, and the two entry points are:

```text
launcher.restore.execute_restore(request, config, paths)
launcher.restore.recover_incomplete_restore(database_path, backup_dir, config, paths)
```

## 16.1. Module boundary

```text
launcher/restore/
  phases.py         the twelve phases and the complete transition graph
  contracts.py      typed request/result/outcome types and the fixed message set
  state.py          the durable operation record and its atomic publication
  workspace.py      the isolated operation directory and ownership rules
  instance_lock.py  the exclusive launcher-instance lock
  staging.py        source intake and the staged read-only candidate
  validation.py     the complete candidate-validation contract
  capacity.py       the disk-space preflight
  safety_copy.py    the mandatory verified `before_restore` copy
  replacement.py    target journal handling and the atomic boundary
  verification.py   bounded backend startup, reads and restartability
  engine.py         orchestration ordering
  recovery.py       the startup recovery matrix
```

One bounded backend addition, `backend/app/db/migration_lineage.py`, reads and
classifies a candidate's migration history **without creating the migration
table**. The expected chain still comes from `app.db.migrations`; there is no
second migration registry, no new migration and no schema change.

## 16.2. Operation-state location and ownership

```text
<user data base>/restore/
  launcher.lock                  exclusive launcher-instance lock
  operation.json                 the one authoritative operation record
  .cwos-restore.<random>.tmp     transient publication scratch (launcher-owned)
  <operation-id>/                one isolated directory per attempt
    candidate.sqlite             the staged read-only candidate
```

Placement mirrors `resolve_backup_dir` exactly: the user-data `restore/`
directory when the database is the resolved user database or
`COSMETIC_WORKSHOP_USER_DATA_DIR` is set, otherwise a `restore/` directory beside
the configured development database. The record is never inside the SQLite
working database, the repository, the application package, frontend storage or an
AuditLog table.

**Allowed persisted fields — the complete closed set:**

```text
operation_id
phase
created_at
updated_at
staged_candidate_filename
safety_copy_filename
```

Reading rejects any record whose field set differs, so a record this launcher did
not write is never acted on. There is no `replacement_happened`, no
`rollback_completed` and no `restore_succeeded`: both facts are derived from
`phase`. No raw absolute selected-source path is stored — the staged relative
identity is sufficient.

Cleanup removes only paths that resolve inside the Restore directory and match
the launcher's own scratch prefix and suffix. Symlinks are never followed out of
the boundary, and the verified safety copy lives in `backups/`, outside every
cleanup path.

## 16.3. Atomic state publication and its durability limits

```text
create an exclusively-owned scratch file in the same directory (mkstemp, O_EXCL)
→ write the complete record
→ flush the process buffer
→ os.fsync the file descriptor
→ os.replace onto operation.json        <- the atomic publication boundary
→ best-effort os.fsync of the parent directory
→ remove only the scratch file this call created
```

`os.replace` is POSIX `rename(2)` within one directory: a reader sees the
complete old record or the complete new one, never a mixture. Interruption before
it leaves the old record intact plus one orphan scratch file that
`clean_owned_temp_files` recognizes. An in-place truncate-and-rewrite is not used
anywhere.

**Durability is claimed only as far as the primitive proves it.** `os.fsync`
pushes the file's data out of the operating-system cache. On macOS it does *not*
guarantee the drive flushed its own write cache — that would need `F_FULLFSYNC` —
so **no power-loss durability is claimed**. What is proved, and what the recovery
matrix depends on, is old-or-new atomicity across process death and OS crash.

The parent-directory `fsync` is best-effort: some platforms and mounts refuse an
`O_RDONLY` directory fsync, and refusing to continue there would break Restore on
a filesystem whose atomic boundary is perfectly sound. A failure is tolerated and
does not lose the published record.

Supported platforms: macOS and Linux. Windows is not supported and is not
claimed.

## 16.4. Exclusive launcher-instance lock

`fcntl.flock(LOCK_EX | LOCK_NB)` on `<restore dir>/launcher.lock`. One boundary
covers ordinary startup, Restore execution and incomplete-operation recovery, so
a second launcher cannot begin recovery while the first is mid-replacement. The
kernel releases it when the holder dies, so a killed launcher leaves no stale lock
to clear by hand. The lock file's contents are diagnostic only and are never read
as authority.

The existing port-conflict check is unchanged and keeps its own message. It is
**not** the Restore lock: the backend is stopped during Restore by design, so a
free port proves nothing.

## 16.5. Disk-space preflight formula

Charged per artifact to the filesystem that will hold it, then grouped by device
(`st_dev`) and compared once per device against `shutil.disk_usage(...).free`:

```text
staged candidate        → Restore operation directory  : source_size
operation-state scratch → Restore directory            : 1 MiB
replacement artifact    → working-database directory   : source_size
before_restore copy     → backup directory             : working_database_size
before_migration copy   → backup directory             : source_size
                                            per device : + 16 MiB overhead
```

Two deliberate conservatisms: the `before_migration` allowance is **always**
charged, because the preflight must run before staging and therefore before the
candidate's schema level is known; and the **selected source's filesystem is never
charged**, because Restore writes nothing there and the user's backup may sit on
a nearly full removable volume. A destination whose device or free space cannot be
read counts as unsatisfied. Nothing is deleted to make room — no old user backup
is ever removed.

## 16.6. Target WAL/SHM/journal handling

Run after `safety_copy_verified` and before `replacement_intent`, because it is a
checkpoint against the working database:

1. open the target — this alone completes any pending hot-journal rollback;
2. `PRAGMA journal_mode = WAL` — switching *into* WAL is what removes a rollback
   journal through SQLite; setting `DELETE` directly leaves a rolled-back hot
   journal on disk;
3. `PRAGMA wal_checkpoint(TRUNCATE)` — every committed frame is folded into the
   main file, which is what makes the round trip lossless;
4. `PRAGMA journal_mode = DELETE` — leaving WAL removes `-wal` and `-shm`;
5. close, then **verify** that the three exact owned sidecar paths are gone.

If any sidecar survives, the launcher **stops** rather than unlinking it.
Committed WAL data is real user data, and no file the launcher cannot account for
is ever deleted. Depending on the persisted phase this ends at `aborted` (before
the boundary) or `recovery_blocked` (during recovery).

## 16.7. Replacement boundary

The working database is never replaced from the user-selected path, and never
from the staged candidate — that file is preserved as recovery evidence. A
launcher-owned replacement artifact is created in the working database's own
directory, so publication is one atomic same-filesystem `os.replace`. The target
must equal the exact configured application database path, must exist and must not
be a symlink; anything else is refused before an artifact is created.

Destructive ordering: durable `replacement_intent` → `os.replace` → durable
`replacement_committed`. A persisted `replacement_intent` is always treated as
though replacement may have occurred; no timestamp, size, filename, inode,
migration version or apparent content is inspected to resolve it.

## 16.8. Backend verification endpoints

Started through the existing `launcher.runtime.start_backend_process` boundary,
pinned to the exact `COSMETIC_WORKSHOP_DB_PATH`. Readiness is polled within an
explicit bound (30 s, 0.2 s interval, 10 s per request) rather than slept for, and
a child that exits is reported immediately instead of waiting out the bound.

```text
GET /api/health
GET /api/settings/status
GET /api/settings/workshop-profile
```

The whole cycle runs **twice** with a graceful stop in between — that is the
restartability proof — and the repository fallback database is fingerprinted
before and after, so a child that resolved its own database fails verification.
Response bodies are checked and discarded; they never reach user-facing output.

## 16.9. Browser gate

`launcher.runtime.run_local_runtime` resolves any persisted Restore operation
**before** startup migrations, before the backend child and before the browser. An
unsafe phase never falls through: `recovery_blocked` returns exit code `3`,
starts nothing and opens nothing, and reports one fixed non-technical Russian
sentence. A recovered previous workspace reports that Restore failed — never that
it succeeded.

## 16.10. Developer-only verification

```bash
scripts/c4_i_restore_smoke.sh <exact-published-head-sha>
```

A **developer verification tool**, not a product workflow and never documented as
one. It refuses to run unless HEAD is exactly the expected published SHA and the
workspace is clean, verifies cleanliness again afterwards, works only inside a
temporary directory removed by its trap, and never touches real user data. It
covers a successful Restore against a real backend (including restartability,
source immutability, safety-copy retention and browser non-opening) and a crash at
the destructive boundary recovering through `rollback_in_progress` to
`rolled_back`. The complete phase and fault matrix lives in the automated tests.
