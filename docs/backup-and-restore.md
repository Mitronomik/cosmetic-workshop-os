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
C4-I — IMPLEMENTED ON PR BRANCH — FOURTH CORRECTION APPLIED — NOT MERGED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

This section records **exactly what the branch implements**. It adds no decision:
every rule above still governs, and `C4-I` implements the accepted state machine
of § 7 without renaming a phase, omitting `replacement_intent` or substituting an
equivalent of its own. **Four independent audits** have run against it, finding
**twenty findings in total — 5 + 5 + 7 + 3**, each round against the correction
the previous round produced. All twenty are closed, and none required a change to
the accepted phase machine. § 16.13 records the second round, § 16.14 the third
and § 16.15 the fourth.

There is **no** Restore API endpoint, button, dialog, file picker, frontend route
or product terminal workflow. The engine is internal Python called by a future
`C4-II`:

```python
context = LauncherLifecycleContext.acquire(config, paths)   # lock + canonical paths
execute_restore(RestoreRequest(selected_source), context)   # one attempt
recover_incomplete_restore(context)                          # before ordinary startup
```

## 16.1. Module boundary

```text
launcher/restore/
  phases.py         the twelve phases and the complete transition graph
  contracts.py      typed request/result/outcome types and the fixed message set
  durability.py     the one safety-critical filesystem publication primitive
  state.py          the narrow durable record
  workspace.py      the isolated operation directory and ownership rules
  instance_lock.py  the exclusive launcher-instance lock
  context.py        the lifecycle authority: canonical paths + backend ownership
  staging.py        source intake and the staged read-only candidate
  validation.py     the complete read-only workspace-validation contract
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

## 16.2. The launcher lifecycle context, and what a caller may supply

**Exactly one value comes from the future Restore caller: the selected source.**
`RestoreRequest` has one field. Every destructive or application-owned path is
derived by `LauncherLifecycleContext.acquire()` from the launcher's own
resolvers:

```text
database path     ← app.services.startup.startup_database_config(mode)
backup directory  ← app.services.backup.resolve_backup_dir(config)
Restore directory ← RestoreWorkspace.for_database(database path)
lock path         ← the same workspace
```

One database identity therefore produces the lock, the operation record, the
safety copy and the replacement target. A caller that could name the target could
take the lock for one workspace and replace a database in another while every
individual check passed, because each was asked about a path the caller chose.

`verify_derived_paths()` re-derives all of them and compares, so a context mutated
after construction is refused before any staging. The replacement target is
checked by **re-resolving it from the startup resolver**, not by comparing a
value with a copy of itself.

Development mode remains supported and isolated: with `COSMETIC_WORKSHOP_DB_PATH`
set, `restore/` and `backups/` sit beside the configured development database and
never in the real Documents directory.

## 16.3. Backend-stop proof

Restore may not touch the working database until the ordinary backend is
**provably** stopped. Three things are not proof, and none is used:

- the launcher instance lock — the backend child never takes it;
- a free backend port — during Restore the port is free *by design*;
- having asked a process to exit — asking is not observing.

The proof has **two** parts, and the second is not implied by the first.

**Process ownership.** `run_local_runtime` hands the child it starts to
`context.backend`, so the launcher holds the exact `Popen`. `stop_backend()`
sends `SIGTERM`, waits within a bound, escalates to `kill()` **on the same
handle**, waits again, and returns a `BackendStopProof` only once `poll()` shows
the process actually exited.

**The backend-liveness lock.** An in-memory handle dies with the launcher. After
a *hard* launcher crash — `SIGKILL`, panic, power loss — the uvicorn child keeps
running and keeps the database open, while the next launcher owns nothing and
would otherwise conclude that nothing was running.

So the backend process itself holds `<restore dir>/backend-liveness.lock` for its
whole lifetime, taken from the exact path the launcher passes in
`COSMETIC_WORKSHOP_BACKEND_LIVENESS_LOCK`. The kernel releases an `fcntl.flock`
when the holder dies, for any reason, with no cleanup code of ours involved — so
a held lock means a live backend, whoever started it, and a free lock means none.
That is a fact about the operating system's process table rather than about
anything this application remembered to write down.

**The retained maintenance lease.** A lock that is checked and released proves
availability at an instant and reserves nothing:

```text
launcher checks the lock            ← free
launcher releases it
another backend acquires it         ← nothing prevented this
launcher settles the SQLite journal
launcher replaces the working database
```

Every step reports success and a live writer holds the database throughout. So
the launcher takes that same canonical lock and **keeps** it —
`BackendMaintenanceLease` — for the whole destructive interval: safety-copy
creation, journal settlement, replacement-artifact preparation, working-database
replacement, rollback replacement and post-replacement filesystem verification.
While the lease is held no backend can start against this workspace, because the
child's own acquisition is the thing that would have to succeed.

`stop_backend()` therefore stops the owned handle, waits for the lock to be
released, and then **takes and retains** the lease. `require_backend_stopped()`
requires that lease to still be held, before journal settlement and before every
replacement including rollback. A released lease is a refusal even when the stop
proof is intact and no backend is running: an unreserved workspace is not
authority for destructive work.

**Pre-import acquisition.** Taking the lock in the FastAPI lifespan takes it after
Python has imported uvicorn, `app.main`, every router and the database layer.
Everything before that is a window in which a launcher-managed backend exists and
holds nothing:

```text
launcher spawns the child
→ child is importing the application, holding no lock
→ launcher dies hard
→ the next launcher sees a free lock and begins destructive work
→ the delayed child finishes importing and opens the database underneath it
```

Launcher-managed children therefore run `python -m app.launcher_backend_entrypoint`,
which acquires the lock **before importing any application module** and exits
without ever reaching `app.main` when it cannot. The lifespan acquisition remains
as an idempotent defence; it is simply no longer the first acquisition point.

**The exact-child handshake.** Owning a `Popen` says the launcher started a
process; it does not say the process took the lock. The entrypoint reports its
acquisition over a pipe the launcher created for that one spawn, carrying a token
generated for that one spawn, and `start_owned_backend_process` returns only once
that report arrives. Both halves are one-run values, so stale evidence cannot
satisfy a later start and a replayed token is refused. Timeout, EOF, an early
child exit and a foreign token are the same answer: the child is stopped, no
browser opens and Restore does not proceed. Health is checked as well, never
instead — it answers after the import this mechanism exists to gate. No PID file,
no port, no process-name discovery.

**The verification cycle.** Verification is the one part of Restore that must
start a backend, so the lease is released for exactly **one owned-backend
lifetime** at a time and taken back at the end of it:

```text
release the maintenance lease
→ start the owned child through the pre-import lock entrypoint
→ wait for that exact child's lock-acquired handshake
→ verify
→ stop the child by its owned handle
→ wait for the lock to be released
→ reacquire the maintenance lease
→ only then continue, replace or roll back
```

The scope of that release is one backend lifetime and nothing more. Startup
initialization and migrations run **under the retained lease**: they open and
rewrite the working database with no backend involved, so there is nobody to hand
the lock to, and releasing it there would simply leave the database unreserved
while it was being written. And because verification is two cycles, it is two
releases and two reacquisitions — never one release spanning both. Between the
two children the lock is free, and an unleased launcher would be letting a
separate backend into the workspace it is about to replace.

```text
startup / migrations                       lease held
cycle 1  release → child → stop → reacquire
                                           lease held   ← the between-cycle moment
cycle 2  release → child → stop → reacquire
continue, replace or roll back             lease held
```

At every moment one of two things is true: the launcher holds the maintenance
lease, or one exact launcher-owned child holds the canonical lock and has
completed the exact-child handshake. Never neither.

The lease is reacquired on the failure path too, because the failure path leads to
rollback and rollback replaces the working database. A reacquisition that fails
blocks recovery; it never proceeds to a replacement without the lease. The
handoff is implemented in exactly one place —
`LauncherLifecycleContext.owned_backend_window()`, which refuses to open unless
the lease is held — and the verifier is given it as a required `run_backend_cycle`
parameter, so "release once, start twice" cannot be expressed without going around
the launcher entirely.

**An orphan is detected, never killed.** This launcher did not start it, so it
has detection but no authority: Restore and startup recovery refuse, nothing is
replaced, no second backend starts and the browser stays closed. Killing a
process discovered by PID file, port, name or pattern is not a safety measure —
it is a second failure mode — and a future support flow, not `C4-I`, is where a
user is told to close the other window.

**And an orphan is refused as a result, never as an exception.** An orphan is the
exact condition this gate exists to notice, so startup recovery returns a typed
`RecoveryResult` with `normal_startup_allowed=False`, the fixed
`RECOVERY_BLOCKED_MESSAGE` and the phase that is really on disk.
`run_local_runtime` branches on that and returns `RESTORE_BLOCKED_EXIT_CODE`.
Nothing starts, the browser never opens, the working database and the operation
record are untouched, no transition is attempted, and the user sees one sentence
rather than a traceback — every technical detail stays in the local log. This
holds both with an interrupted Restore record present and with no record at all:
with no Restore ever attempted, the orphan alone is still reason to refuse,
because ordinary startup would put a second writer on one SQLite database.

**Recovery is resolved before the port is checked.** A real orphan is a running
backend, so it holds the canonical liveness lock **and** it is still listening on
the configured port. Checking the port first therefore turned the most likely
real orphan into a `RuntimeLaunchError` about a busy port — an exception, a
traceback, and a message telling the user to close another window — while the
typed blocked result built for exactly this case never ran. The launcher order is:

```text
build runtime config and paths
→ acquire the launcher lifecycle
→ resolve Restore recovery and canonical backend liveness
→ if blocked: fixed message, RESTORE_BLOCKED_EXIT_CODE, no backend, no browser
→ assert the configured port is available
→ ordinary startup and migrations, under the maintenance lease
→ release the lease for the exact owned backend child
→ open the browser only after a safe start
```

The port check is not weakened by moving: an unrelated program on the configured
port with the canonical lock free is an ordinary collision, recovery runs
normally, and the same `RuntimeLaunchError` and the same user-facing port message
follow. No backend starts and no browser opens in either case. An occupied port
is never reinterpreted as a Restore problem.

When the environment variable is absent — the ordinary test client, a developer
importing the app — no lock is taken and nothing is claimed. When it is present
and the lock cannot be taken, backend startup fails rather than putting a second
writer on one SQLite database.

Nothing discovers a process by port, name or command-line pattern. `pkill`,
`lsof`, `pgrep` and `killall` are absent from `context.py`, `maintenance_lease.py`
and `backend_handshake.py`, and tests enforce that against each module's
executable source.

Backends started for verification are owned by `verify_restored_backend` — one
per cycle, each inside its own owned-backend window — and stopped in a `finally`,
on the failure path too. `recovery_blocked` starts nothing.

## 16.4. Operation-state location and ownership

```text
<user data base>/restore/
  launcher.lock                  exclusive launcher-instance lock
  operation.json                 the one authoritative operation record
  .cwos-restore.<random>.tmp     transient publication scratch (launcher-owned)
  <operation-id>/                one isolated directory per attempt
    candidate.sqlite             the staged read-only candidate
```

Placement mirrors `resolve_backup_dir` exactly. The record is never inside the
SQLite working database, the repository, the application package, frontend
storage or an AuditLog table.

**Allowed persisted fields — the complete closed set:**

```text
operation_id
phase
created_at
updated_at
staged_candidate_filename
safety_copy_filename
```

Reading rejects any record whose field set differs. There is no
`replacement_happened`, no `rollback_completed` and no `restore_succeeded`: both
facts are derived from `phase`. No raw absolute selected-source path is stored.

**Only a previously completed record may be replaced.** `create()` admits exactly
the positive `SAFE_TERMINAL_STARTUP_PHASES` vocabulary — `completed`, `aborted`,
`rolled_back` — and refuses everything else, including every live phase and an
unreadable record.

`recovery_blocked` is refused specifically. It is terminal but it is not
*completed*: it is the authoritative pointer to an operation nothing could
resolve, and it names the staged candidate and the safety copy that a support
procedure needs. Grouping it with the other terminal phases let an ordinary new
attempt overwrite that pointer and start past a blocked recovery. Clearing a
blocked recovery is a separately authorized support procedure — outside `C4-I`,
and not something pressing Restore again may do.

`operation_id` must be a **canonical launcher-generated UUID4** — the backend's
own `is_canonical_operation_id` round-trip, plus the version check, plus the safe
relative-filename rule. An arbitrary safe filename is not enough, because the
value becomes a directory name; a record carrying one blocks startup.

Cleanup removes only paths that resolve inside the Restore directory and match
the launcher's own scratch prefix and suffix, plus the one deterministically
named replacement artifact. Symlinks are never followed out of the boundary, and
the verified safety copy lives in `backups/`, outside every cleanup path.

## 16.5. The durability primitive, and its honest limits

One shared module, `launcher/restore/durability.py`, publishes the operation
record, the staged candidate, the working-database replacement and the rollback
replacement:

```text
exclusive scratch creation (O_CREAT | O_EXCL)
→ complete write
→ flush the userspace buffer
→ flush the file to durable media       (F_FULLFSYNC on macOS, else fsync)
→ atomic same-directory os.replace       <- the publication boundary
→ flush the published target
→ flush the parent directory             <- MANDATORY
```

**The parent-directory flush is not best effort.** `os.replace` makes the new
content visible atomically but does not make the *rename* survive a host
interruption. Ignoring that failure is what could leave the working database
replaced while the operation record reverted to a phase saying nothing was
replaced — and startup recovery would then take the `aborted` branch over a
database that is not the one it thinks it is.

Failures are therefore **classified, never swallowed**:

| Stage | Meaning | Required response |
|---|---|---|
| `BEFORE_REPLACE` | Nothing was published. | Treat as not having happened. |
| `DURING_REPLACE` | `os.replace` failed; ambiguous. | Treat as possibly published. |
| `AFTER_REPLACE` | The rename landed; durability unproven. | Re-read the record; for a database replacement, roll back. |

`RestoreStateError.published` and `ReplacementError.may_have_replaced` carry that
verdict. After any publication that may have landed, the engine **re-reads the
authoritative record** and acts on the phase actually there. It never transitions
to `aborted` over a record that may already say `replacement_intent`.

**Confirming an already-published record.** `os.replace` can succeed while the
flush after it fails: the new phase *is* visible, and only its durability is
unproven. Rewriting would be wrong — the content is already correct, and a
rewrite means another scratch file and another rename — so
`confirm_existing_durability()` re-flushes the existing file and its parent
directory, changing nothing. It is used after a post-rename failure and again
before ordinary startup is allowed from any terminal phase. When it fails, the
actual phase is kept, evidence is kept, startup is blocked, and the next launcher
start retries.

**What is claimed, and how it is checkable.** On macOS `F_FULLFSYNC` asks the
drive to flush its own write cache — the strongest flush the platform offers;
plain `fsync` on macOS does not. Where the filesystem reports
`ENOTSUP`/`EINVAL`/`EOPNOTSUPP` the call falls back to `fsync`. Any other error
propagates rather than being downgraded. Directories are flushed with `fsync`
only — `F_FULLFSYNC` on a directory descriptor is unsupported and is not
attempted, and it is recorded separately as `directory_fsync` so evidence never
conflates the two.

**"Records that it did" is literal.** Every safety-critical flush reports its
publication category, whether the target was a file or a directory, the platform
and the method that ran, into `DURABILITY_DIAGNOSTICS` and the technical log. A
claim that the stronger primitive is used "where supported" is only honest if a
reader can check which one happened on their machine. The categories are
`operation_record`, `record_durability_confirmation`, `staged_candidate`,
`replacement_artifact`, `working_database_replacement` and
`rollback_replacement`. The diagnostics carry **no** path, filename, database
content or user data, and are deliberately **not** part of the authoritative
operation record: the flush method is evidence about a write, not a lifecycle
fact, and has no place in the phase machine.

Supported platforms: macOS and Linux. Windows is not supported and nothing is
claimed for it. No power-loss guarantee is claimed anywhere.

## 16.6. Exclusive launcher-instance lock

`fcntl.flock(LOCK_EX | LOCK_NB)` on `<restore dir>/launcher.lock`. One boundary
covers ordinary startup, Restore execution and incomplete-operation recovery. The
kernel releases it when the holder dies, so a killed launcher leaves no stale
lock. The lock file's contents are diagnostic only and are never read as
authority. The existing port-conflict check is unchanged and keeps its own
message.

## 16.7. Source intake, sidecars and staging identity

**Sidecars are checked beside the original selected source**, before the copy
begins and again after it completes, before `candidate.sqlite` is published:

```text
<source>-wal
<source>-shm
<source>-journal
```

Any of them, present by `lexists` (so a symlinked or dangling sidecar counts),
rejects the source. Checking beside the *staged* candidate cannot catch this —
staging copies only the main file, so a live WAL's committed rows would simply
never be staged and `PRAGMA quick_check` would still return `ok`. The accepted
`C4-I` source is a self-contained backup artifact; converting a live WAL database
into one is a different operation and is not authorized here.

Nothing unlinks, checkpoints, migrates, renames or repairs the selected source or
its sidecars. A hot rollback journal is rejected *before* the file is opened,
precisely because opening it would roll the journal back — a write to the user's
selected file.

**The copy reads a held descriptor, twice.** Intake opens the source once with
`O_RDONLY | O_NOFOLLOW` and keeps that descriptor; both passes read it with
`os.pread` and neither re-opens the path.

Stat identity alone is not enough. Device, inode, size and file type describe
*which file* this is, not **what is in it** — a writer can rewrite bytes in place,
keeping the same inode and the same total length, and all four stay identical. The
staged candidate would then hold pages from two different source states, and
`PRAGMA quick_check` would very likely still call it `ok`, because every page is
individually well-formed.

Two mechanisms close that. `st_mtime_ns` and `st_ctime_ns` joined the recorded
identity, which catches the ordinary case cheaply. And the copy is verified by
**two independent SHA-256 passes**: the first hashes exactly the bytes written into
the staging scratch file, the second re-reads the same descriptor from offset zero
and hashes without writing. A digest or byte-count mismatch rejects the source.
The digest comparison is the load-bearing one, because it does not depend on
filesystem timestamp resolution.

```text
pre-copy stat + sidecar check
→ pass one: pread → staging scratch, hashing what is written
→ stat + path + sidecar revalidation
→ pass two: pread the same descriptor, hashing only
→ compare byte counts and digests
→ final stat + path + sidecar revalidation
→ publish candidate.sqlite
```

A path replaced, a file rewritten in place, a symlink substituted, a size change
or a sidecar appearing — in any window — all fail before publication, and no
candidate is left behind.

## 16.8. Disk-space preflight formula

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

The `before_migration` allowance is always charged, because the preflight must
run before staging and therefore before the candidate's schema level is known.
The selected source's filesystem is never charged. A destination whose device or
free space cannot be read counts as unsatisfied. Nothing is deleted to make room.

## 16.9. Safety copy

Taken by the existing ADR 0015 SQLite Online Backup engine under the canonical
reason `before_restore`. No `shutil.copy2`, no second backup implementation, no
`artifact_audit_operations` row and no AuditLog event.

Verification reuses `validate_workspace_snapshot` — the **same** read-only
checker the staged candidate passes: regular non-symlink file, non-empty,
read-only open, structural check, a known ordered migration prefix, recognizable
workspace identity, the required tables for that prefix, and no external sidecar
dependency. A safety copy verified more weakly than a candidate would be a
recovery point that might not be one, and it is the artifact the entire
destructive boundary rests on.

## 16.10. Target journal handling, replacement and verification

**Journal settlement** runs after `safety_copy_verified`, after backend-stop
proof, and before `replacement_intent`: open the target (completing any hot
journal rollback) → `journal_mode = WAL` (which is what removes a rollback
journal through SQLite; setting `DELETE` directly measurably leaves one behind) →
`wal_checkpoint(TRUNCATE)` (folding committed frames into the main file) →
`journal_mode = DELETE` (removing `-wal`/`-shm`) → close → **verify** the three
exact owned sidecar paths are gone. A surviving sidecar stops the operation;
nothing is blind-unlinked.

**Replacement** is never from the selected path and never from the staged
candidate (preserved as evidence). A launcher-owned artifact with a
**deterministic** name — `.cwos-restore-<operation-id>.replacement`, exclusively
created beside the working database — is published with one durable atomic
rename. The name is derived rather than random so startup recovery can name the
one artifact it owns and remove exactly that, with no directory globbing beside
the user's database. `recovery_blocked` preserves it as evidence.

**Verification** starts the child through the existing
`launcher.runtime.start_backend_process` boundary, pinned to the exact
`COSMETIC_WORKSHOP_DB_PATH`, with bounded readiness polling (30 s, 0.2 s interval,
10 s per request) and then:

```text
GET /api/health
GET /api/settings/status
GET /api/settings/workshop-profile
```

The whole cycle runs **twice** with a graceful stop between — the restartability
proof. The repository fallback database is fingerprinted before and after with
**SHA-256 plus size plus stat identity**; existence, size and mtime alone would
miss a same-size write inside one timestamp granularity, which is exactly what a
child quietly migrating the repository database looks like.

## 16.11. Browser gate and result honesty

`run_local_runtime` resolves any persisted Restore operation **before** startup
migrations, the backend child and the browser. `recovery_blocked` returns exit
code `3`, starts nothing and opens nothing, and reports one fixed non-technical
Russian sentence.

Results distinguish three separate facts, because a failed publication can make
them disagree:

```text
outcome                 what the engine concluded it was doing
durable_phase           the phase actually on disk
normal_startup_allowed  whether the launcher may continue
```

`restore_succeeded` requires all three to agree: outcome `completed`, durable
phase `completed`, **and** startup permitted. Claiming success while refusing to
start the application is a mixed message a future `C4-II` screen cannot render
honestly.

**Ordinary startup is permitted positively**, by an allow-list, through one
shared function used by every caller:

```text
permits_ordinary_startup(durable_phase, record_exists, durability_confirmed)
```

- **no record at all** — permitted; no Restore was ever attempted here;
- `completed`, `aborted`, `rolled_back` — permitted **only** once that record's
  durability has been confirmed;
- everything else — blocked. That includes the four *unresolved* pre-replacement
  phases. `prepared`, `source_staged`, `candidate_validated` and
  `safety_copy_verified` are safe for the **database**, because replacement never
  happened, and unsafe for **startup**, because the operation is still live and
  recovery has not closed it. A negative rule — "not in the unsafe set" — reads as
  if it means the same thing and silently admitted all four;
- an unreadable or unparseable record — blocked, because "I cannot tell what
  happened" is not a state to start from.

**Terminal records are never transitioned again**, not even to themselves. A
post-rename flush failure at `completed` therefore re-reads the record, confirms
its durability, and returns — it never reaches the abort path, which would have
attempted `completed → aborted`, an edge the graph does not contain, and would
have rolled back a database that had already been restored and verified. The same
holds for `aborted`, `rolled_back` and `recovery_blocked`.

**The initial `prepared` publication is equally ambiguous.** If `create()`
renames and then its flush fails, a `prepared` record exists on disk. It is never
reported as "no record": the engine re-reads, closes it as `aborted` where it
can — an edge the graph does authorize — and otherwise blocks startup so the next
launcher start closes it. Ordinary startup never proceeds while `prepared`
remains persisted.

**And the re-read checks whose record it found.** The rename may simply never have
landed, leaving the *previous* operation's terminal record in place:

```text
operation A ends at `completed`
operation B is generated
B's `prepared` publication fails ambiguously
the record on disk still says A / completed
```

Reading that as this attempt's outcome would report a Restore that never staged a
byte as a success, carrying another operation's identity. So `operation_id` is
compared first. When it differs, the attempt was never published, and:

- the previous record is never transitioned, rewritten or cleaned;
- its outcome is never inherited — the result is `aborted`, always, with the fixed
  `PREPARATION_NOT_PUBLISHED` sentence saying the attempt did not start;
- the result keeps **this** attempt's operation ID, so it cannot be mistaken for a
  report about the previous operation;
- only this attempt's own freshly created, empty operation directory is cleaned;
- whether ordinary startup may then proceed is the previous record's question,
  answered by the same positive rule — its durability is re-proved without
  modifying it, and a `recovery_blocked`, live or unprovable record blocks.

**A visible `completed` whose durability cannot be confirmed is described
truthfully.** The restored data are in place and verified, `completed` is on disk,
and only the flush that would make that rename survive a host interruption is
unproved. Nothing was rolled back — there was nothing to roll back from — and
nothing was lost. Reporting the rollback sentence there claimed two things that
did not happen, so the window has one fixed category of its own,
`COMPLETION_DURABILITY_UNCONFIRMED`, whose message says the data were restored and
verified, that the technical finalization could not be completed safely, that all
data are preserved, and that reopening the application retries the confirmation.
It is not a phase and not a transition: `phase` stays `completed`,
`restore_succeeded` stays false while startup is refused, and the next start
reports an ordinary success once the confirmation succeeds.

## 16.12. Verification of this slice

`C4-I` is verified by the automated backend and launcher suites plus a
**developer-only exact-head smoke runner that lives outside the pull request**.
The project smoke-authoring contract requires a PR-specific runner to sit outside
the code it verifies, so no such script is committed here — an earlier revision of
this branch committed one under `scripts/` and it has been removed. `C4-III` may
later introduce a reviewed, reusable smoke framework; that is a separate decision
and a separate pull request.

The external runner checks out the exact published head into a detached worktree
outside the repository, runs against that checkout, records only PIDs it started
itself, terminates only those PIDs, classifies its result as
`PASS — FULL AUTOMATED SMOKE PASSED`, `FAIL — PRODUCT`, `INCONCLUSIVE — RUNNER`
or `INCONCLUSIVE — ENVIRONMENT`, and retains its evidence outside the repository.
`scripts/restore_backup.sh` is unrelated to `C4-I` and is unchanged.

## 16.13. Second correction — what the second audit found

The first audit found five gaps in the original implementation and they were
closed. A second audit then ran against that correction and found five more, all
in code the first round had introduced or left in place. All five are closed on
the same branch, and **none required a change to the accepted phase machine**.

| Finding | Closed by |
|---|---|
| A post-rename failure publishing `completed` fell through to the abort path and attempted `completed → aborted`, an edge the graph does not contain. | Terminal records are never transitioned again (§ 16.11). A dedicated terminal handler re-reads, confirms durability and returns. |
| Unresolved pre-replacement phases were treated as permitting ordinary startup, because permission was derived negatively. | One positive allow-list, `permits_ordinary_startup(...)`, used by every caller (§ 16.11). |
| A same-size in-place rewrite of the selected source kept device, inode, size and type identical and escaped the identity checks. | Timestamps joined the identity, and staging now proves content stability with two independent SHA-256 passes over the held descriptor (§ 16.7). |
| A hard launcher crash lost the in-memory process handle, so an orphaned backend appeared absent. | A backend-liveness lock held by the backend process itself for its whole lifetime (§ 16.3). |
| The `F_FULLFSYNC` fallback was described as "recorded" but was not. | Every safety-critical flush records its category, target kind, platform and method (§ 16.5). |

Two of these are worth stating as standing rules rather than fixes.

**Detection is not authority.** An orphaned backend blocks Restore and startup
recovery; it is never killed. This launcher did not start it, and killing a
process discovered by PID file, port, name or pattern is a second failure mode
rather than a safety measure. A future support flow — not `C4-I` — is where a
user is told to close the other window.

**Nothing claims more than it can prove.** `restore_succeeded` requires a durable
`completed` *and* permission to start. The recorded flush method is the one that
ran, not the one intended. And no power-loss guarantee is claimed anywhere: what
is proved is old-or-new atomicity across process death and OS crash, plus the
strongest flush the platform actually performed.

## 16.14. Third correction — what the third audit found

A third independent audit ran against the second correction and found seven
findings — four safety gaps and three reporting gaps — all in code the earlier
rounds had introduced or left in place. All are closed on the same branch, and
**none required a change to the accepted phase machine**: the twelve phases, the
transition graph and `phase` as the sole authoritative lifecycle field are
unchanged.

| Finding | Closed by |
|---|---|
| The backend-liveness lock was checked momentarily and released, so nothing prevented a backend from starting during the destructive interval. | A retained launcher maintenance lease over the same canonical lock, required by `require_backend_stopped()` (§ 16.3). |
| The lock was acquired in the FastAPI lifespan, leaving the whole application import as a window in which a launcher-managed child held nothing. | `app.launcher_backend_entrypoint` acquires the lock before importing any application module, proved to the launcher by a bounded one-run handshake (§ 16.3). |
| An orphaned backend made `RestoreLifecycleError` escape startup recovery, where the caller expects a `RecoveryResult`. | A typed blocked `RecoveryResult`, with or without an interrupted record present (§ 16.3). |
| An ambiguous initial `prepared` publication could report a *previous* operation's terminal record as this attempt's outcome. | The operation ID is compared before anything is concluded; a foreign record is never inherited and never modified (§ 16.11). |
| `RestoreOperationStateStore.create()` treated `recovery_blocked` as replaceable, letting a new attempt overwrite the pointer to an unresolved operation. | Only the positive `SAFE_TERMINAL_STARTUP_PHASES` vocabulary is replaceable (§ 16.4). |
| A visible-but-unconfirmed `completed` was reported with the rollback sentence, claiming a rollback that did not happen. | One fixed `COMPLETION_DURABILITY_UNCONFIRMED` category saying only what is known (§ 16.11). |
| One pre-correction test node ID had been renamed rather than preserved, so a historical guarantee could not be tracked across the correction. | The historical node `test_unsafe_phases_never_permit_ordinary_startup` is restored; corrections are additive to the node set. |

Three standing rules come out of this round.

**Availability is not reservation.** A lock that is checked and released answers
"was it free at that instant" and nothing about the interval afterwards. Every
destructive step now runs under a lock that is *held*, and the retained lease is
itself the authority — not a memory of having once seen the lock free.

**A process is not proved by owning its handle.** Starting a child says the
launcher started something; it does not say that something took the lock. The
handshake is what joins those two facts, and it is bounded, one-run and
unforgeable by replay. A health endpoint cannot substitute: it answers after the
import the handshake exists to gate.

**Identity is checked before an outcome is read.** A record on disk is only this
attempt's record if it carries this attempt's operation ID. A previous
operation's `completed` is not a new attempt's success, and a `recovery_blocked`
record is a pointer to be preserved rather than a terminal state to be replaced.

## 16.15. Fourth correction — what the fourth audit found

A fourth independent audit ran against the third correction and found two safety
gaps and one reporting gap. Both safety gaps are in the *boundaries* of
mechanisms the earlier rounds got right — where the lease is released, and where
recovery sits in the startup order — rather than in the mechanisms themselves.
All are closed on the same branch, and **none required a change to the accepted
phase machine**: the twelve phases, the transition graph and `phase` as the sole
authoritative lifecycle field are unchanged.

| Finding | Closed by |
|---|---|
| The maintenance lease was released around the entire startup-plus-two-cycle verification block, rather than around each exact owned-backend lifetime. | Startup and migrations run under the retained lease; each verification cycle is its own release/handshake/stop/reacquire window (§ 16.3). |
| `run_local_runtime()` checked the port before Restore recovery, so a real orphan holding both the canonical liveness lock and the configured port bypassed the typed blocked `RecoveryResult`. | Recovery and backend liveness are resolved before the port check; the port check keeps its own message for the ordinary collision (§ 16.3). |
| The pull-request body carried inconsistent finding counts and did not describe this correction. | One consistent accounting: twenty findings across four independent audits, 5 + 5 + 7 + 3. |

Two standing rules come out of this round, and both are about scope rather than
about mechanism.

**A correct primitive can still be held over the wrong interval.** The retained
lease, the pre-import lock acquisition and the exact-child handshake were all
right; what was wrong was how much they were asked to cover at once. A release
wide enough to span two backend lifetimes leaves the lock free in the middle, and
a release that covers migrations hands the workspace to nobody at all. The
invariant is now stated positively: at every moment either the launcher holds the
lease, or one exact owned child holds the canonical lock having completed the
handshake — never neither.

**Order the checks by what they actually prove.** A free port is not proof that
nothing owns the workspace, and an occupied port is not proof that the owner is
something to refuse for. The canonical lock answers ownership, so it is consulted
first; the port answers "is this address usable", so it is consulted after, and it
keeps its own unchanged message for the ordinary collision it really describes.
