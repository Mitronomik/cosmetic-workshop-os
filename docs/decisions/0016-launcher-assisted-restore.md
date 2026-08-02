# ADR - Launcher-assisted transactional Restore

## Status

`ACCEPTED` — 2026-08-02. Recorded as `CR-010 — Decide launcher-assisted Restore semantics`.

This ADR closes the product-decision gap that kept `C4 — Restore и recovery`
inactive. It records a product decision and a durable contract. It **does not
implement Restore** and changes no runtime code.

| Item | Status |
|---|---|
| `CR-010` — launcher-assisted Restore semantics | `ACCEPTED — NOT IMPLEMENTED` |
| `C4-I` — launcher-owned restore safety engine | `AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED` |
| `C4-II` — user-facing launcher Restore flow | `PLANNED — NOT AUTHORIZED` |
| `C4-III` — Restore end-to-end verification and lifecycle closure | `PLANNED — NOT AUTHORIZED` |
| Restore | `NOT IMPLEMENTED` |
| macOS packaging | `NOT COMPLETED` |
| Safe packaged update flow | `NOT COMPLETED` |
| Full release-candidate smoke | `NOT COMPLETED` |
| Product release readiness | `NOT CLAIMED` |

Surrounding lifecycle at acceptance:

```text
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED — NOT IMPLEMENTED
C4 — ACTIVE DECISION COMPLETED / IMPLEMENTATION NOT STARTED
```

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

Before **any** mutation of the current workspace, the selected backup must be
validated from a **staged read-only copy**. Validating the user's original file
in place is not acceptable, because validation must never be able to touch the
source.

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
→ create an isolated restore-operation directory
→ copy the selected source into a launcher-owned staging file
→ validate the staged candidate
→ create and verify the pre-restore safety copy
→ persist the restore-operation phase
→ atomically replace the working database from a file staged in the same
  filesystem/directory boundary
→ start the application against the exact restored database path
→ run migrations when required
→ verify startup and basic reads
→ mark Restore completed
→ clean only launcher-owned temporary staging files
```

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
recovery, such as:

- a backend-generated operation ID;
- safe relative launcher-owned filenames;
- the current Restore phase;
- timestamps;
- whether database replacement occurred;
- whether rollback completed.

It must **not** persist:

- database contents;
- client information;
- arbitrary user-authored text;
- credentials;
- raw absolute source paths when a staged relative identity is sufficient;
- SQL errors or stack traces.

On launcher startup, an incomplete Restore operation must be detected **before
the normal backend starts**. If replacement occurred but successful completion
was not durably recorded, the safe default is to restore the pre-restore safety
copy before exposing the ordinary application UI, unless the implementation can
prove an equivalent deterministic and tested recovery result.

An interrupted Restore may never be ignored.

If rollback cannot be completed safely, the launcher must:

- not start the ordinary application;
- preserve the safety copy, staged candidate and operation evidence;
- show a fixed non-technical recovery message;
- direct the user to support-assisted recovery;
- delete no evidence automatically.

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

**The browser UI must not be opened into the normal workspace before this gate
passes.** Showing the workspace is the product's implicit success signal, and it
must not precede the evidence.

### 10. Rollback

If any failure occurs after database replacement but before successful
completion, the launcher must:

1. stop the partially started backend;
2. preserve diagnostic evidence without exposing it to the user;
3. restore the pre-restore safety copy through the same launcher-owned safe
   replacement boundary;
4. verify the rolled-back database can start;
5. report that Restore did **not** complete and that the previous workspace was
   recovered.

Rollback is not optional. If rollback succeeds, the user must **not** be told
that Restore succeeded. If rollback fails, the product must not continue with an
uncertain database.

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
AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
```

This is the **only** runtime slice authorized by this decision. Its future scope:

- launcher-owned restore operation domain vocabulary;
- source and staged-candidate validation;
- schema-lineage compatibility validation;
- pre-restore safety-copy orchestration using the existing safe backup engine;
- isolated restore operation directory;
- durable narrow Restore operation state;
- same-filesystem staging;
- atomic working-database replacement;
- automatic rollback;
- incomplete-operation recovery before backend startup;
- backend/database-path continuity;
- backend startup and bounded health verification;
- focused backend/launcher tests;
- isolated exact-head launcher smoke.

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
Rejected: one narrow launcher-owned record is enough for deterministic recovery,
and the project has repeatedly refused generic frameworks for bounded problems
(`CR-009`, ADR 0013).

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
technically open will be rejected.

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
