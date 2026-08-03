# ADR - Launcher-assisted transactional Restore

## Status

`ACCEPTED` — 2026-08-02. Recorded as `CR-010 — Decide launcher-assisted Restore semantics`.

This ADR closes the product-decision gap that kept `C4 — Restore и recovery`
inactive. It records a product decision and a durable contract. It **does not
implement Restore** and changes no runtime code.

| Item | Status |
|---|---|
| `CR-010` — launcher-assisted Restore semantics | `ACCEPTED` |
| `C4-I` — launcher-owned restore safety engine | `IMPLEMENTED ON PR BRANCH — SIXTH CORRECTION APPLIED — NOT MERGED` |
| `C4-II` — user-facing launcher Restore flow | `PLANNED — NOT AUTHORIZED` |
| `C4-III` — Restore end-to-end verification and lifecycle closure | `PLANNED — NOT AUTHORIZED` |
| Restore | `NOT IMPLEMENTED` |
| macOS packaging | `NOT COMPLETED` |
| Safe packaged update flow | `NOT COMPLETED` |
| Full release-candidate smoke | `NOT COMPLETED` |
| Product release readiness | `NOT CLAIMED` |

Surrounding lifecycle:

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4 — ACTIVE
C4 product decision — COMPLETE
C4-I — IMPLEMENTED ON PR BRANCH — SIXTH CORRECTION APPLIED — NOT MERGED
C4-II — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
```

**This decision itself is unchanged.** `C4-I` implements the state machine below
exactly — same twelve phases, same transition graph, same recovery matrix, same
`replacement_intent` rule — and required no deviation, so no amending decision was
needed. The implementation's own operational detail (state-file location, the
publication primitive and its durability limits, the disk-space formula, target
journal handling and the verification endpoints) is recorded in
`docs/backup-and-restore.md` § 16, not restated here.

This ADR does not reopen `CR-004`, `CR-005`, `CR-006`, `CR-007`, `CR-008` or
`CR-009`, and it does not reopen ADR 0011, 0012, 0013, 0014 or 0015. It adds no
migration, no API endpoint, no AuditLog event and no dependency.

---

## Context

The product is local-first. The user's only recovery path is a local SQLite
backup file in the user data directory, and `CR-004` (ADR 0015) established that
those backups are now transactionally consistent snapshots taken through the
SQLite Online Backup API. Creating a backup has been safe since `C3-II-B3`
merged.

Consuming one has never been decided. `docs/implementation-plan.md` § C4 offered
exactly two options and picked neither:

```text
1. safe user-facing restore в приложении/launcher; либо
2. support-assisted restore без терминала для конечного пользователя.
```

The historical `docs/roadmap.md` PR23 sketch proposed an optional
`POST /api/restore`. That sketch predates the launcher, the migration system and
the artifact-audit ledger, and it is not a viable design: the process that would
serve the request holds the database it would have to replace.

Three facts make Restore different from every operation the product performs
today:

1. **The target is the open working database.** Uvicorn keeps the SQLite main
   database open, potentially with a `-wal` and `-shm` beside it. Replacing that
   file underneath a live connection is exactly the class of behaviour `CR-004`
   classified as `HIGH` severity in the opposite direction.
2. **The operation is destructive to the current working state.** Unlike a
   backup, an export or a report document, Restore discards data. There is no
   version, archive or reversal to fall back on — only a copy taken beforehand.
3. **The operation spans a crash boundary.** Database replacement, backend
   startup and verification cannot be one SQLite transaction, so an interrupted
   Restore can leave the workspace in a state no in-database record can
   describe, because the database that would hold the record is the thing being
   replaced.

The primary user is non-technical. The product contract forbids requiring Git,
Python, Node.js, Docker, SQLite tools, GitHub or a terminal for ordinary use, and
that constraint applies to recovery most of all — recovery is exactly when the
user is least able to follow developer instructions.

---

## Decision

```text
MVP Restore is launcher-assisted.

Restore is not performed by a running FastAPI backend endpoint and is not
implemented as an ordinary SPA mutation.

The launcher owns process shutdown, backup validation, the pre-restore safety
copy, staging, atomic database replacement, post-restore startup verification,
rollback, and incomplete-restore recovery.
```

Support-assisted recovery remains a **fallback** for failures that cannot be
resolved automatically. It is not the primary MVP Restore workflow, and it is
never the design target.

The user must never need Git, Python, Node.js, Docker, SQLite tools, GitHub or a
terminal to restore a backup.

### Why the launcher and not the backend

The launcher already owns the lifecycle boundary this operation needs. ADR 0006
made it the single supervised entry point; it resolves the user data directory,
takes the `before_migration` backup, runs migrations before the API is served,
starts the uvicorn child against an explicit `COSMETIC_WORKSHOP_DB_PATH`, and
opens the browser only once startup succeeded. Restore needs precisely those
powers plus the ability to have no backend running at all, which a backend
request by definition cannot have.

Assigning Restore to a FastAPI route would require the API process to close its
own database, replace it, reopen it and report on the result through a
connection that no longer exists. Assigning it to the SPA would put a
destructive, crash-sensitive filesystem transaction behind a browser tab that
can be closed or reloaded mid-operation, and would make the frontend the lock
holder for a resource it cannot observe.

---

## Accepted Restore product contract

### 1. Restore source

Restore accepts a **locally selected SQLite backup** that passes the
application-owned validation contract. The selected source may be:

- a current manual backup produced by the application;
- a historical application backup from a supported schema version;
- a backup copied to another local directory or external drive.

**The backup filename is not sufficient proof that the file is valid.** The
canonical `CR-005` filename grammar identifies artifacts this application
generated; it says nothing about the bytes inside them, and a foreign file may
be placed at any path.

Restoring the following is **not authorized**:

- JSON exports;
- CSV or XLSX files;
- report documents;
- arbitrary unknown SQLite databases;
- a directory;
- a symbolic link;
- a cloud URL;
- a network service;
- a partial set of tables.

**Restore is whole-database only.** There is no partial-table import, no merge,
no selective record recovery and no row-level undo. Those are different products
with different safety contracts, and none of them is decided here.

The selected source file is **read-only input**. It must never be modified,
renamed, migrated, deleted or rewritten by Restore, including on the failure and
rollback paths. After a successful Restore the selected backup must remain
byte-identical to what the user chose.

### 2. Process ownership

Restore must run while the normal application backend is **stopped**.

The launcher must:

1. prevent a second application instance from starting;
2. stop the current backend cleanly when it is running;
3. confirm that the database is no longer in active application use;
4. perform Restore outside the ordinary API process;
5. start the backend only after the restore transaction reaches the verification
   stage;
6. open the ordinary browser UI only after Restore succeeds completely.

The following are **not authorized**:

- replacing the database from a running FastAPI request;
- frontend coordination as the locking mechanism;
- a hidden terminal command as the user workflow;
- direct database replacement while Uvicorn still has the database open.

### 3. Backup validation

```text
The staged candidate must pass the complete Restore validation contract
before any mutation, replacement, deletion or migration of the current
working database.
```

The selected backup is validated from a **staged read-only copy**. Validating
the user's original file in place is not acceptable, because validation must
never be able to touch the source.

Staging is Restore infrastructure, not a mutation of the business workspace:

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

**`PRAGMA quick_check = ok` alone must not be treated as sufficient proof.**
`CR-004` established the counter-examples directly: an empty file returns `ok`,
a WAL-era raw copy missing every committed row returns `ok`, and a copy holding
two transaction states at once returns `ok` with the row count intact. A healthy
but unrelated SQLite database also returns `ok`.

A backup from a **newer unsupported schema must be rejected before the current
database changes**. Opening it optimistically would let a future schema meet an
older application, and no migration path runs backwards.

An **older but known and migratable schema may be accepted**. The candidate
itself stays immutable; ordinary application migrations operate only on the
restored working copy after replacement.

### 4. Explicit confirmation

Restore is destructive to the current working state, so it requires a two-step
user flow:

```text
select backup
→ validate and show human-readable backup information
→ explicit destructive confirmation
→ execute Restore
```

The confirmation screen must clearly state:

- which backup was selected;
- when it was created, when that can be established safely;
- that current workshop data will be replaced;
- that a safety copy of the current database will be created first;
- that the selected backup will remain unchanged;
- that the application will restart;
- that the operation must not be interrupted.

**Validation failure must never show the destructive confirmation action as
available.** A user cannot be allowed to confirm the replacement of their
workspace with a file the application could not validate.

Raw SQL, migration IDs, internal paths, stack traces and SQLite messages must not
appear in the ordinary user-facing result. This follows the existing rule that
technical detail belongs in local logs.

### 5. Mandatory pre-restore safety copy

Before replacing the current database, the launcher must create a
**transactionally consistent safety copy** of the current database, using the
already accepted safe SQLite backup engine from ADR 0015. `shutil.copy2` must not
be reintroduced for SQLite contents.

The safety backup reason is the existing canonical system reason:

```text
before_restore
```

This reason is already reserved in `docs/domain-model.md`; Restore uses it rather
than inventing a new vocabulary.

The safety copy:

- must complete and pass verification **before** database replacement;
- must remain available after a successful Restore;
- must not be silently deleted;
- is a system recovery artifact, not the selected Restore source;
- must not require a new generic backup service;
- must not create a false success if its creation or verification fails.

If the current database exists and the safety copy cannot be created **and**
verified, Restore stops before replacing anything. The selected source backup
remains unchanged.

### 6. Staging and atomic replacement

The working database must **not** be replaced directly from the user-selected
path. The user's file may live on a removable drive, on a slow or disconnecting
volume, or on a different filesystem, and it must never be consumed as the live
working file.

Required sequence:

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

Each bracketed value is the authoritative `phase` of § 7.1, persisted through the
crash-safe boundary of § 7.3 **before** the next action begins.

The replacement mechanism must not silently overwrite an unrelated foreign file.
The same ownership reasoning `C3-II-B3` applied to backup publication applies
here: an existence check followed by a write is not an ownership guarantee.

The implementation may use a same-directory atomic replacement primitive, but it
must be **proved by tests and isolated smoke**, not asserted.

**Filesystem replacement and SQLite are not one transaction, and no document may
claim they are.** The atomic step is the filesystem rename boundary only.
Everything after it — startup, migration, verification — is outside it, which is
exactly why durable operation state and rollback are mandatory.

### 7. Durable Restore operation state

A crash can occur between safety-copy creation, database replacement, startup
verification and completion. Exactly one narrowly scoped, launcher-owned Restore
operation record is authorized, stored **outside the working database** —
because the working database is the thing being replaced.

It is **not**:

- a generic workflow engine;
- a job queue;
- an outbox;
- a cloud state store;
- an application-wide transaction framework.

The durable state may contain only the minimum required for deterministic
recovery:

- a launcher-generated operation ID;
- safe relative launcher-owned filenames;
- **the authoritative `phase`** (§ 7.1);
- timestamps.

It must **not** persist:

- database contents;
- client information;
- arbitrary user-authored text;
- credentials;
- raw absolute source paths when a staged relative identity is sufficient;
- SQL errors or stack traces.

**`phase` is the sole authoritative lifecycle field, and it is mutually
exclusive.** Facts such as *whether database replacement occurred* and *whether
rollback completed* are **derived from `phase`** and must never be persisted as
independent authoritative fields, because two independent fields can contradict
each other and the recovery decision would then have no single source of truth.

An interrupted Restore may never be ignored. On launcher startup, an incomplete
Restore operation must be detected and resolved **before the normal backend
starts**, exactly as § 7.5 requires.

### 7.1. Authoritative phase vocabulary

Exactly twelve phases exist. They are internal machine values, written in
lowercase ASCII with underscores. No alias, no prose-only synonym, and no
additional phase is authorized by `CR-010`.

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

#### `prepared`

The launcher has generated the operation ID, created the isolated launcher-owned
operation directory, and durably created the initial operation record. It has
**not** yet established a complete staged candidate, and it has **not** changed
the current working database.

#### `source_staged`

The launcher-owned staged candidate has been copied and durably published inside
the isolated operation directory. The user-selected source remains unchanged, and
the current working database remains unchanged. The candidate has **not** yet
passed the complete application-owned Restore validation contract.

#### `candidate_validated`

The staged candidate passed the complete accepted validation contract of § 3:
regular local file; no symlink or path escape; read-only SQLite open; non-empty;
structural checks; recognizable application workspace; known ordered
migration-history prefix; no unknown, duplicated, reordered or skipped migration
IDs; not newer than the running application; required tables for the recorded
schema level; no external journal dependency; no mutation and no silent repair.

The current working database remains unchanged.

#### `safety_copy_verified`

The mandatory pre-restore safety gate of § 5 completed. A transactionally
consistent safety copy of the current working database exists and passed its
accepted verification contract. The working database has **not** yet entered the
replacement boundary.

If the application does not support Restore without an existing working
database, that case is rejected **before** this phase rather than silently
weakening the safety-copy requirement.

#### `replacement_intent`

Durably persisted **immediately before** entering the atomic working-database
replacement boundary. It means:

```text
replacement may not yet have happened,
may be in progress,
or may already have happened.
```

This phase deliberately represents an **ambiguous crash window**. On startup it
must always be treated conservatively as requiring rollback from the verified
safety copy before the ordinary application may start.

The launcher must **never** infer from filenames, timestamps or the apparent
contents of the working database that replacement did or did not happen.

#### `replacement_committed`

The atomic filesystem replacement call returned successfully, and the launcher
then durably recorded that the replacement boundary completed.

The restored working database is still **unverified** and is **not** yet
authoritative for ordinary product use. The ordinary browser UI remains blocked.

#### `verification_in_progress`

The launcher durably recorded this phase **before** starting the backend,
migrations or post-restore verification against the replaced working database.

The restored database remains **provisional**. A crash or failure in this phase
requires rollback.

#### `completed`

All accepted post-restore checks of § 9 passed and completion was durably
recorded: exact restored database path continuity; required migrations
completed; backend start; database open; health; bounded representative
read-only endpoints; no unexpected fallback database; restartability; the
selected source remains byte-identical; the safety copy remains available.

**Only this phase makes the restored working database authoritative for ordinary
use, and the browser may be opened only after `completed` has been durably
recorded.**

#### `aborted`

The operation ended **before** `replacement_intent`. The current working
database remains authoritative and was never replaced.

Only launcher-owned staging and operation files may be cleaned, subject to exact
ownership checks. A verified safety copy, when one was already created, must not
be silently deleted.

`aborted` is a **terminal non-destructive** result.

#### `rollback_in_progress`

Rollback has been durably requested **before** the launcher enters the rollback
replacement boundary. The launcher must restore the verified pre-restore safety
copy through the same safe launcher-owned replacement boundary.

This operation must be idempotent or safely repeatable after a crash. The
ordinary backend and browser remain blocked.

#### `rolled_back`

The safety copy was restored to the exact working database path and the previous
workspace passed the required rollback verification.

**Restore did not succeed.** The previous workspace is authoritative again, and
ordinary startup may proceed only after rollback verification passes. Future
`C4-II` must present a truthful user-facing result stating that Restore failed
and the previous workspace was recovered.

`rolled_back` is a **terminal failed-Restore** result, never successful Restore.

#### `recovery_blocked`

The launcher cannot prove that the working database or the rollback result is
safe. It must:

- not start the ordinary backend;
- not open the ordinary browser workspace;
- preserve the safety copy;
- preserve the staged candidate;
- preserve the operation record;
- preserve local diagnostic evidence;
- avoid automatic deletion;
- return a fixed non-technical support-assisted recovery result.

`recovery_blocked` is **terminal for automatic recovery**. Only a separately
defined support procedure may move the installation out of this condition.

### 7.2. Allowed transitions

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
prepared
→ aborted

source_staged
→ aborted

candidate_validated
→ aborted

safety_copy_verified
→ aborted
```

Rollback:

```text
replacement_intent
→ rollback_in_progress

replacement_committed
→ rollback_in_progress

verification_in_progress
→ rollback_in_progress

rollback_in_progress
→ rolled_back

rollback_in_progress
→ recovery_blocked
```

Terminal phases:

```text
completed
aborted
rolled_back
recovery_blocked
```

**No other transition is authorized by `CR-010`.** The following are explicitly
prohibited:

```text
replacement_intent → completed
replacement_committed → completed
verification_in_progress → ordinary startup without completed
rollback_in_progress → completed
rolled_back → completed
recovery_blocked → ordinary startup
aborted → replacement_intent
```

A new Restore attempt is a **new operation with a new operation ID**. A terminal
operation record is never reactivated.

### 7.3. Crash-safe persistence ordering

**General rule.** Every phase transition must be persisted through one
documented and tested crash-safe launcher-owned write boundary **before** the
launcher begins the next action whose recovery behaviour depends on that phase.

**An in-place truncate-and-rewrite of the only operation record is not
sufficient.** The exact filesystem primitive is selected in `C4-I`, but it must
provide:

- a complete old record **or** a complete new record after interruption;
- no partially written authoritative record;
- an atomic publication boundary;
- documented handling of durability for the file and its parent directory;
- tests with faults injected at every publication boundary.

Do not claim stronger filesystem durability than the selected platform primitive
can prove.

**Required destructive ordering.** The launcher must:

1. durably record `replacement_intent`;
2. only then enter the atomic working-database replacement boundary;
3. after the replacement call succeeds, durably record `replacement_committed`;
4. durably record `verification_in_progress`;
5. only then start the backend, migrations and post-restore checks;
6. durably record `completed` only after all checks pass;
7. open the ordinary browser only after durable `completed`.

**Required rollback ordering.** The launcher must:

1. stop any partially started backend;
2. durably record `rollback_in_progress`;
3. only then enter the rollback replacement boundary;
4. verify the restored previous workspace;
5. durably record `rolled_back`;
6. only then permit ordinary startup of the recovered previous workspace.

If the launcher cannot durably persist a required transition, it must not
continue to the next destructive step. If failure happens after replacement but
before `completed`, the operation must enter or recover through rollback.

### 7.4. The `replacement_intent` crash rule

```text
A persisted replacement_intent is treated as though replacement may have
occurred, even when the current working file appears unchanged.
```

The launcher must **not** try to resolve this ambiguity by inspecting:

- modification timestamps;
- file size alone;
- filenames;
- inode identity alone;
- migration version alone;
- the apparent business contents of the working database.

The safe outcome is **rollback from the verified safety copy**.

This rule exists because the window

```text
persist replacement intent
→ atomic replacement
→ persist replacement committed
```

cannot be observed from the outside after a crash. Every heuristic that might
close it is unsound: a replacement that succeeded can leave a file that looks
untouched by size or timestamp, a replacement that never ran can leave a file
that looks recent, and the restored candidate is by construction a valid
workspace database, so its contents prove nothing about which file is present.
Guessing wrong in one direction silently keeps a half-replaced workspace; the
conservative rule costs one rollback in a rare case and is never wrong.

### 7.5. Mandatory startup recovery matrix

Every persisted phase has exactly one required startup behaviour. This table is
the accepted MVP recovery behaviour, not a default that an implementation may
replace.

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

`C4-I` is an **implementation of this state machine**, not an opportunity to
invent an alternative one. No wording such as *"unless the implementation can
prove an equivalent result"* weakens this table.

### 8. Schema migration boundary

Restore and migration are distinct responsibilities.

The launcher restores a validated working copy. The normal startup migration
system may then migrate an older supported restored schema. Existing migration
invariants remain mandatory:

- a backup must exist before migration;
- migrations are ordered;
- migrations must not silently mutate historical business meaning;
- migration failure must not produce a false successful Restore;
- a newer-than-current schema is rejected **before** replacement.

No second migration framework is authorized for Restore, and the selected source
backup is never migrated.

### 9. Post-restore verification

Restore is successful only after **all** required verification passes. At
minimum:

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

**The browser UI must not be opened into the normal workspace until `completed`
has been durably recorded.** Showing the workspace is the product's implicit
success signal, and it must not precede the evidence.

### 10. Rollback

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
7. report that Restore did **not** complete and that the previous workspace was
   recovered.

Rollback is not optional, and it is entered from `replacement_intent`,
`replacement_committed` or `verification_in_progress` only. If rollback
succeeds, the user must **not** be told that Restore succeeded — `rolled_back`
is a failed Restore. If rollback fails, the product must not continue with an
uncertain database; it enters `recovery_blocked` and stops.

### 11. AuditLog boundary

**No Restore AuditLog event is authorized by this decision.** In particular
`restore.completed` is **not** implicitly authorized.

A Restore AuditLog event requires a separately explicit C4 decision, because the
database that would contain the event is itself being replaced and migrated.
Writing an event into the database being discarded records nothing, and writing
one into the restored database asserts a business action the restored database
never performed.

Filesystem operation-state evidence is **not** AuditLog. It is launcher recovery
metadata with a different owner, a different lifetime and a different privacy
contract, and it must not be presented in `Журнал действий`.

### 12. User data and privacy

Restore preserves the local-first product boundary:

- no backup contents, database contents, client data, recipe data, contact data
  or workshop profile data may be uploaded anywhere;
- no network connection is required for Restore;
- user-visible errors are fixed, human-readable and non-technical;
- technical detail belongs only in local logs and must not appear in the
  ordinary UI.

---

## Backend boundary

There is no backend implementation in this decision. The future boundary is:

- **no ordinary FastAPI Restore mutation endpoint**;
- the backend must be **stopped** during replacement;
- normal backend startup and migration services remain authoritative after
  replacement;
- post-restore verification may use existing health and read endpoints;
- no business repository writes are authorized as part of validation;
- no new Restore AuditLog event is authorized;
- no new migration is authorized by this decision.

No speculative backend interfaces are created here beyond what the accepted
product contract requires.

## Frontend boundary

There is no frontend implementation in this decision:

- ordinary SPA routes do not own database replacement;
- the final user-facing Restore flow belongs to the launcher/application shell;
- the SPA must not attempt to coordinate a restore lock;
- the frontend must not parse SQLite, migrations, database paths or backup
  contents;
- `C4-II` will later define the user-facing launcher flow;
- no Restore route, button, dialog or API call is authorized here.

---

## C4 subdivision

### C4-I — Launcher-owned restore safety engine

```text
IMPLEMENTED ON PR BRANCH — SIXTH CORRECTION APPLIED — NOT MERGED
```

This is the **only** runtime slice authorized by this decision. Its scope:

- launcher-owned restore operation domain vocabulary;
- source and staged-candidate validation;
- schema-lineage compatibility validation;
- pre-restore safety-copy orchestration using the existing safe backup engine;
- isolated restore operation directory;
- the **exact twelve-phase durable Restore operation state** of § 7.1, with
  `phase` as the sole authoritative lifecycle field;
- the **exact transition graph** of § 7.2;
- the **crash-safe persistence ordering** of § 7.3, including a publication
  boundary proved by fault-injection tests;
- same-filesystem staging;
- atomic working-database replacement, preceded by durable `replacement_intent`;
- automatic rollback through `rollback_in_progress`;
- **the complete startup recovery matrix of § 7.5**, resolved before backend
  startup;
- backend/database-path continuity;
- backend startup and bounded health verification;
- focused backend/launcher tests;
- isolated exact-head launcher smoke.

`C4-I` implements the accepted state machine **exactly**. It must not:

- rename phases;
- omit `replacement_intent`;
- infer replacement from filesystem appearance;
- start the ordinary backend from an unsafe phase;
- expose the ordinary browser before durable `completed`;
- treat `rolled_back` as successful Restore;
- recover `recovery_blocked` automatically by guessing;
- use independent contradictory replacement/rollback booleans;
- use an in-place rewrite as the sole authoritative operation-state persistence
  mechanism.

Any proposed deviation requires a **new explicit documentation decision before
runtime implementation**.

`C4-I` must **not** expose a final user-facing Restore entry point yet, and must
provide **no terminal workflow** to the product user. Its implementation surface
is internal launcher infrastructure for the future user-facing flow.

`C4-I` must not modify frontend production code unless repository evidence proves
a minimal shared contract module is unavoidable. Any such need must be documented
before implementation rather than assumed.

### C4-II — User-facing launcher Restore flow

```text
PLANNED — NOT AUTHORIZED
```

Reserved future scope: file selection; validation progress; human-readable backup
summary; explicit destructive confirmation; progress and restart states;
successful completion screen; rollback-completed screen; support-assisted failure
screen; keyboard and accessibility behaviour; narrow-viewport behaviour where
applicable; no terminal requirement.

### C4-III — Restore end-to-end verification and lifecycle closure

```text
PLANNED — NOT AUTHORIZED
```

Reserved future scope: complete exact-package Restore smoke; older supported
schema Restore; current schema Restore; corrupt/foreign/newer-schema rejection;
interruption recovery; post-replacement startup failure and rollback; repeated
launch after successful Restore; selected source immutability; safety-copy
retention; C4 lifecycle closure.

---

## Rejected alternatives

**`POST /api/restore` on the running backend.** The historical `docs/roadmap.md`
PR23 sketch. Rejected: the process serving the request holds the database the
request must replace. It cannot close it, cannot report on the result after
closing it, and cannot recover if the replacement fails mid-way. This option is
now explicitly superseded.

**SPA-owned Restore with a coordination lock.** Rejected: the frontend cannot
observe process state or filesystem ownership, a browser tab can be closed or
reloaded mid-operation, and `CR-004` already rejected frontend coordination as a
lock for a much weaker operation than this one.

**Support-assisted recovery as the primary MVP design.** Rejected as the primary
design: it makes the user's only recovery path depend on a developer being
available and on instructions the primary user cannot safely follow. It is
retained as the **fallback** for failures that cannot be resolved automatically.

**A documented manual terminal procedure.** Rejected: a terminal command must not
become the permanent product workflow, and recovery is precisely when the
non-technical user is least able to execute one correctly.

**Direct replacement from the user-selected path, without staging.** Rejected:
the source may be on another filesystem or removable volume, an atomic
same-directory replacement would be impossible, and a failure mid-copy would
destroy the working database with no complete replacement available.

**Optimistic replacement with no pre-restore safety copy.** Rejected: it makes
the destructive step irreversible and turns any post-replacement failure into
permanent data loss.

**Treating `PRAGMA quick_check = ok` as validation.** Rejected on `CR-004`
evidence: empty files, WAL-era copies missing every committed row, and unrelated
healthy databases all return `ok`.

**Optimistically opening a newer-than-current schema.** Rejected: no migration
runs backwards, and the failure would be discovered only after the working
database was already gone.

**A generic operation framework, job queue or outbox for Restore state.**
Rejected: one narrow launcher-owned record with twelve fixed phases is enough for
deterministic recovery, and the project has repeatedly refused generic frameworks
for bounded problems (`CR-009`, ADR 0013).

**Leaving the phase vocabulary to the implementation.** Rejected: the phases are
a safety-critical contract, not an implementation detail. An undocumented state
machine invented inside `C4-I` would make the crash behaviour of the product's
only recovery path unreviewable, and the one window that matters most —
`replacement_intent` — is exactly the one an implementer is most likely to skip
because it appears redundant.

**Independent durable booleans for "replacement occurred" and "rollback
completed".** Rejected: two independently written flags can disagree after a
crash, and the recovery decision would then have no single source of truth. Both
facts are derived from the mutually exclusive `phase`.

**Resolving the replacement crash window by inspecting the working database.**
Rejected on soundness, not cost — see § 7.4. No timestamp, size, filename, inode
or content check distinguishes "replaced" from "not replaced" after a crash,
because the candidate is by construction a valid workspace database.

**Writing a `restore.completed` AuditLog event as part of this decision.**
Rejected: the database that would hold the event is being replaced. The question
is real and is deferred to a separately explicit C4 decision.

**Partial-table or selective restore.** Rejected for the MVP: it is a different
product with a different safety contract, and nothing in the current evidence
requires it.

---

## Consequences

**Positive.** The user's only recovery path becomes usable without a developer,
a terminal or a support session. The destructive step is bounded by a verified
safety copy on one side and mandatory verification on the other. An interrupted
Restore has a deterministic recovery rather than an undefined workspace. The
decision is compatible with future macOS packaging, because the launcher is
already the packaged entry point.

**Negative and accepted.** Restore requires an application restart, so it is not
an in-session operation. The launcher grows a genuinely more complex
responsibility, including durable state it did not previously own. Two extra
full-size copies of the database exist transiently — the staged candidate and the
safety copy — which costs disk space on a workspace that may be large. Validation
is deliberately strict, so some hand-modified or foreign SQLite files that would
technically open will be rejected. The conservative `replacement_intent` rule
will occasionally roll back a Restore that had in fact already replaced the
database successfully; that costs the user one repeat attempt from an intact,
verified workspace, which is the correct trade against silently keeping a
half-replaced one.

**Unchanged.** Backup creation, JSON export, report documents, the artifact-audit
ledger, migrations, the AuditLog read contract and every accepted `CR-004` /
`CR-005` / `CR-006` / `CR-009` semantic are untouched by this decision.

---

## Non-goals

This decision does not authorize and does not implement: Restore itself; a
Restore API endpoint; a Restore button, dialog or file picker; a
`restore.completed` AuditLog event; a migration; a database replacement; a
backup; a Restore smoke; `C4-I`, `C4-II` or `C4-III` implementation; packaging;
`.app` or `.dmg` creation; an updater; cloud sync; scheduled backups; a
background worker; a generic operation framework; a job queue or outbox; roles or
multi-user support; OCR; accounting; or any claim of product release readiness.

## Verification boundary

This ADR was accepted through a documentation-only pull request. No backend,
frontend or launcher suite was executed for it, no build was run, no smoke was
run and no runtime artifact was created. The accepted PR #168 evidence recorded
alongside this decision belongs to that merged pull request and was **not**
re-executed here.

**`C4-I` verification is separate and belongs to its own pull request.** That
slice implements this decision on an **unmerged branch**: the complete backend and
launcher suites and a developer-only exact-head Restore smoke — run from **outside**
the pull request, against a detached checkout of the exact published head — were
run there, and its evidence is recorded on that pull request rather than restated
in this ADR. An independent review of the first published head found five
safety-critical gaps in the *implementation* (source sidecar handling, backend-stop
proof, canonical destructive paths, rollback-publication failure handling and the
durability boundary). A second audit of that correction found five more (terminal
`completed` publication handling, positive startup permission and the initial
`prepared` ambiguity, same-size in-place source modification, orphaned backends
after a hard launcher crash, and the unrecorded flush method). A third audit of
that second correction found seven more:

- the backend-liveness lock was **checked momentarily and released**, which proves
  availability at an instant and reserves nothing, leaving the whole destructive
  interval open to a backend starting;
- the lock was acquired only in the FastAPI lifespan, so the entire application
  import was a window in which a launcher-managed child held nothing;
- an orphaned backend made `RestoreLifecycleError` escape startup recovery, where
  the launcher expects a `RecoveryResult`, turning a designed refusal into an
  unhandled exception;
- an ambiguous initial `prepared` publication could read a **previous**
  operation's terminal record as this attempt's outcome and identity;
- `recovery_blocked` was grouped with the completed terminal phases and could be
  overwritten by an ordinary new attempt;
- a visible-but-unconfirmed `completed` was reported with the rollback sentence,
  claiming a rollback that did not happen;
- one pre-correction test node ID had been renamed rather than preserved.

A fourth audit of that third correction found three more:

- the maintenance lease was released around the **entire** startup-plus-two-cycle
  verification block rather than around each exact owned-backend lifetime, so the
  canonical lock was held by nobody during startup migrations and again between
  the two verification cycles;
- `run_local_runtime()` checked the configured port **before** Restore recovery,
  so a real orphan — which holds the canonical liveness lock *and* the port —
  raised a busy-port exception instead of producing the typed blocked result;
- the pull-request body carried inconsistent finding counts.

A fifth audit of that fourth correction found two more:

- an unrelated **temporary port collision** could occur before or during rollback
  recovery and turn a retryable environment problem into terminal
  `recovery_blocked`, because the state-mutating recovery ran before the port was
  ever checked;
- the documented handoff invariant claimed **continuous lock ownership at every
  instant**, although a bounded release-to-child scheduling gap necessarily exists.

A sixth audit of that fifth correction found two more:

- a real port collision could occur **after** `assert_port_available()` succeeded
  and **before** uvicorn's actual bind: the child reported a successful start
  while holding only the liveness lock, so the collision arrived as a
  started-then-died child, was classified as a verification failure, and could
  still end a rollback at terminal `recovery_blocked`;
- the test that appeared to cover that race injected the exception at the
  owned-backend start, so it demonstrated exception routing rather than the real
  child, handshake or bind.

All twenty-four are closed: 5 + 5 + 7 + 3 + 2 + 2 across six independent audits.

**None of them required a change to this decision** — the twelve phases, the
transition graph, the recovery matrix and the `replacement_intent` rule are
exactly as accepted here. In particular no condition discovered by any audit
justified a new phase: `completed`-but-unconfirmed, `durability_failed`,
`backend_orphaned` and the newly named `preparation_not_published` and
`completion_durability_unconfirmed` are transient result and diagnostic
categories, not lifecycle facts, and they are reported through the typed result
rather than persisted.

The third correction adds three implementation-level rules that this decision's
§ 2 launcher-ownership requirement already implies and which are now stated
explicitly: the launcher **retains** exclusive backend exclusion for the whole
destructive interval rather than sampling it; a launcher-managed backend acquires
that exclusion **before importing the application** and proves it to the launcher
through a bounded exact-child handshake; and an operation record is only this
attempt's record when it carries this attempt's operation ID. Implementing `C4-I` changes nothing above — no phase was renamed, no
transition added or removed, and no recovery behaviour substituted — and it does
**not** make Restore a shipped product capability. `Restore` stays
`NOT IMPLEMENTED`, `C4-II` and `C4-III` stay `PLANNED — NOT AUTHORIZED`, and
product release readiness stays `NOT CLAIMED`.
