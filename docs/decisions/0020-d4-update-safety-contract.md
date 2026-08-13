# ADR 0020 — D4 Update Safety contract

Status: **ACCEPTED BY CR-013 — DECISION ONLY; D4-A AUTHORIZED NEXT**

Decision base: `dc2301f7d4e101ad0fba851325dae9274f02da0c`
Change request: `CR-013 — D4 Update Safety contract and bounded implementation authorization`

This ADR becomes normative when this changeset is merged to `main`. It contains no D4 runtime implementation.

## Context

`D3 — macOS package MVP` is implemented and `C4-III` is lifecycle-closed. The packaged application already runs the ordinary launcher user-mode startup path, stores user data outside the package, and uses the existing backend startup initialization before the backend and browser are made available.

D4 is the roadmap stage for **safe manual replacement/update of that packaged local application**. It is not a delivery system. The user model is still local-first and offline-capable: close the old package, place/open the newer package, let the application prove compatibility and migrate safely when required, then continue ordinary work.

Current implementation already provides part of the safety baseline:

- `launcher.runtime` owns ordinary startup sequencing;
- `backend/app/services/startup.py` detects pending migrations and creates a `before_migration` SQLite backup before invoking the existing migration runner;
- ADR 0015 requires SQLite Online Backup API semantics instead of raw copying of a live SQLite database;
- D3 package tests prove the packaged application reaches the same startup/migration path;
- `backend/app/db/migration_lineage.py` already provides read-only ordered-lineage classification for Restore candidates, including `schema-newer-than-application`;
- packaged startup already has a fixed Finder-visible fatal-alert mechanism whose user text does not interpolate paths, tracebacks, SQL or exception details.

D4 must strengthen and reuse these seams. It must not create parallel startup, migration, backup, Restore or desktop-shell architectures.

## Existing baseline

### One ordinary startup path

The existing launcher user-mode path remains the only ordinary product startup path. D4 update safety is inserted into that path **before backend start and before browser handoff**.

### Existing before-migration backup

The existing `before_migration` backup primitive is retained. It is transactionally consistent because it uses the SQLite Online Backup API and publishes a completed snapshot rather than raw-copying the working database file.

The current automatic startup backup is not the same audited workflow as a manual backup. D4 therefore does **not** claim that the current automatic backup is already a fully verified UpdateLog-backed artifact. D4-B must add the verification needed to make successful backup creation a hard prerequisite for migration staging.

### Closed Restore boundary

ADR 0016 and ADR 0018 remain authoritative for Restore. Restore is `IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`. D4 is not allowed to reopen its state machine, control transport, source authority, browser interaction or destructive engine.

## Problem

D4 has four unresolved safety problems.

First, application version truth is duplicated and incomplete: the package build has a hard-coded version, backend package metadata has another literal, a historical `app_settings["app.version"]` placeholder exists, and Settings currently has no effective runtime version.

Second, the ordinary startup path does not yet apply the existing read-only lineage classifier as a pre-mutation compatibility gate. An older application must never silently open or mutate a database that is already newer than that application.

Third, direct in-place migration can leave the canonical working database partially changed if a migration process is interrupted or a migration fails after some writes. A backup is necessary, but backup existence alone is not the D4 safety property.

Fourth, a database-only UpdateLog cannot be the only durable update truth because migration can fail before that database can safely serve the backend.

## Decision

D4 uses this control flow for a supported older database:

```text
resolve effective app version
→ read-only compatibility preflight on canonical DB
→ create and verify before_migration backup
→ create runner-owned consistent migration stage
→ apply pending migrations only to the stage
→ verify staged DB and target lineage
→ atomically publish the verified stage as canonical DB
→ durably record completed migration update
→ ordinary backend start
→ ordinary browser handoff
```

Before the database commit point, the old canonical working database remains authoritative and is not mutated by migration execution.

D4 is split into gated slices. **Only D4-A is authorized by this decision.**

## Version identity

There is exactly **one canonical build-time product-version source in the repository**.

D4-A will introduce that immutable repository-owned source. The exact file/module name is an implementation detail of D4-A, but the ownership rules are not:

1. the canonical source is not stored in mutable user data;
2. `Info.plist`, `package-runtime.json` and any backend package/version projection are **generated projections**, not independently editable authorities;
3. inside a built package, a validated packaged projection is the effective runtime version because the repository source is not present as an editable development source;
4. the backend Settings/read-only status surface receives that same effective runtime version;
5. development/unpackaged startup resolves the same repository-owned version source and never invents a separate development version literal;
6. historical `app_settings["app.version"] = "0.1.0"` is a legacy placeholder only. It is **not authoritative** for application identity, compatibility, migration decisions or downgrade decisions.

No hidden SemVer comparison is introduced by D4-A. Version equality/identity is product metadata; schema compatibility is decided by migration lineage.

## Schema compatibility contract

The authoritative schema identity is the complete ordered `schema_migrations` lineage produced by the repository migration chain.

D4 must not introduce a second independently mutable numeric schema-version counter. Human/log presentation may show the last applied migration ID and the target migration ID, but those are compact representations of the ordered lineage, not another source of truth.

D4-A must reuse or generalize the existing read-only lineage semantics in `backend/app/db/migration_lineage.py` rather than creating a conflicting second classifier.

The preflight runs before backup creation, migration execution, backend start and browser open.

Required outcomes:

```text
canonical DB path does not exist
→ ordinary first-run creation path

existing DB with current exact known lineage
→ ordinary startup; no update migration

existing DB with supported older exact known prefix
→ D4 update path

existing DB with complete known lineage plus later application migrations
→ schema-newer-than-application; fail closed before mutation

existing DB with unknown / reordered / skipped / duplicate / unreadable lineage
→ fail closed before mutation

existing SQLite DB with no recognizable migration lineage
→ fail closed; do not reinterpret it as a fresh database
```

"Fresh" means the canonical database file does not exist. A pre-existing unknown file is not fresh.

## Backup-before-migration contract

A supported older canonical database must receive a `before_migration` backup before any migration staging begins.

The backup must reuse the ADR 0015 SQLite Online Backup primitive. Raw copying of the live `.sqlite` file, copying WAL/SHM sidecars, `shutil.copy`, `cp`, or an equivalent filesystem-level database snapshot is forbidden.

D4-B must verify the created backup sufficiently to make it a hard prerequisite for migration staging. If backup creation or verification fails, no stage is created and the canonical database remains authoritative.

The automatic backup does not need a newly invented `BackupRecord` database subsystem merely to satisfy an old conceptual foreign key. Its safe generated backup filename/artifact identity is sufficient for the D4 external UpdateLog.

## Migration failure safety

D4 selects **STAGED MIGRATION + VERIFIED COMMIT**.

The migration stage is not a raw filesystem copy. It is created as a transactionally consistent SQLite snapshot of the canonical working database using the same accepted SQLite backup primitive or a bounded generalization of it.

The stage is:

- runner-owned;
- outside the application package;
- under the external user-data boundary;
- named so it cannot be mistaken for a real backup or the canonical database;
- created on the same filesystem as the canonical database so final publication can be atomic;
- never user-selectable as a Restore source merely because it is a SQLite file.

Pending migrations execute only against the stage. Before commit, D4-B must verify at least:

- the stage opens successfully;
- SQLite structural verification selected by the implementation passes;
- the recorded migration lineage equals the exact application target lineage;
- no unexpected pending migration remains;
- the stage is still the runner-owned artifact selected for this operation.

If staging, migration or verification fails before commit:

- the canonical working database is still the previous authoritative database;
- the `before_migration` backup is retained when it had been created successfully;
- the staged artifact is never promoted;
- the update operation is durably recorded as failed or left as an interrupted `started` operation for conservative reconciliation;
- ordinary backend startup is not allowed to use the failed staged database;
- no browser ordinary-work handoff occurs.

Direct in-place migration is rejected for D4 because the current implementation cannot prove the same "canonical DB untouched before commit" property.

## UpdateLog persistence

D4 `UpdateLog` is **launcher/startup-owned durable update metadata outside the working database**.

It lives under the external user-data directory, not inside the application package and not exclusively inside the SQLite database being migrated. D4-B may implement it as an atomic file-backed journal; the required persistence properties are normative even if the exact filename layout is implementation detail.

Each operation record carries at minimum:

```text
operation_id
from_app_version
to_app_version
from_schema_identity
to_schema_identity
before_migration_backup_identity
started_at
finished_at
status
failure_category
safe_failure_message
```

Allowed terminal statuses are:

```text
completed
failed
```

`started` is the durable non-terminal status. `rolled_back` remains reserved and must not be emitted unless a future separately authorized strategy contains a real rollback transition. The selected staged design normally fails before commit and therefore does not invent rollback.

The journal must be written atomically. It must contain no raw client data, secrets, browser-supplied paths, SQL, raw traceback, or unrestricted absolute filesystem path. The backup reference is a safe generated artifact identity, preferably the generated filename, not a raw absolute path.

### Interrupted `started` operations

A durable `started` record discovered on the next launch is **not automatically equivalent to `failed`** and must never trigger a blind destructive retry.

The next startup performs conservative reconciliation using read-only canonical lineage plus runner-owned artifact ownership evidence:

- canonical lineage still equals the recorded source lineage: treat the migration commit as not completed; retain the old canonical DB; do not auto-retry migration; finalize the interrupted operation as a safe failure only when that conclusion is proven;
- canonical lineage equals the exact recorded target lineage: the atomic database commit occurred even if the journal terminal write was interrupted; reconcile the migration operation to `completed`, then continue only through ordinary runtime-start checks;
- canonical lineage is unknown, newer than the running application, or inconsistent with both recorded source and target: fail closed and require help/recovery guidance;
- orphan runner-owned stage files are ignored as databases and backups. They may be cleaned only after ownership is proven and never become an automatic retry source.

## Update commit point

For D4 the **database update commit point** is the atomic publication/replacement of a fully migrated and verified stage onto the canonical working database identity.

Before that point:

- the old canonical DB is authoritative;
- failure is a migration/update failure;
- the old package may be used only if the unchanged canonical database remains compatible with it.

At publication:

- the stage and canonical target are on the same filesystem;
- D4-B must ensure no application-owned SQLite connection remains open against the canonical database;
- publication must not mix a stage with stale canonical WAL/SHM/journal state;
- the publication operation must have an explicit failure outcome and must not report success unless the canonical identity now refers to the verified target database.

After that point:

- the migrated DB is authoritative;
- a later backend/listener/runtime failure is **not** recorded as "migration failed";
- migration/update status and ordinary runtime-start status are distinct truths.

## Interruption and repeated-launch behavior

D4-B must test and implement conservative behavior for:

- interruption before backup completion;
- interruption after backup but before stage creation;
- interruption during stage creation;
- interruption during staged migration;
- interruption after stage verification but before commit;
- interruption at or immediately after atomic commit;
- interruption before terminal UpdateLog write;
- repeated launch after completed update;
- repeated launch after failed/interrupted update.

No incomplete scratch file may be treated as a backup or canonical database. No repeated launch may automatically perform a blind destructive retry.

## User-facing success and failure truth

D4 does not create a technical update administration screen.

After a successful ordinary backend start, the existing human-facing product UI may expose a small read-only status through Settings/status:

- current application version;
- whether the latest startup required a schema migration;
- successful migration/update confirmation;
- safe failure/recovery guidance when applicable.

The browser is not an update authority and receives no raw filesystem path or update operation authority.

Update/migration failures happen before the ordinary backend/browser may be available. D4-C therefore extends the existing packaged fixed-message failure mechanism (or an equally bounded launcher-owned mechanism), instead of creating a second product UI.

The Finder-visible message is fixed Russian product copy and must not expose:

- absolute paths;
- database filenames unless product support explicitly requires a safe artifact name;
- SQL;
- migration IDs/internal lineage details;
- operation IDs;
- traceback/exception text.

It must truthfully explain that ordinary work was not started on an unverified database, that a safety backup was retained when one had been created successfully, and what the user should do next.

It may say that the working database is unchanged **only on a control-flow path that proves the update commit point was never crossed**.

## Manual package update contract

D4 is a manual package-replacement safety flow, not an updater downloader.

Intended user sequence:

```text
close old app
→ keep the previous package temporarily
→ place/open newer packaged app
→ newer app uses the same external user-data directory
→ compatibility preflight
→ safe staged migration when required
→ successful ordinary startup
→ only then consider discarding the previous package
```

Keeping the previous package until the first successful launch is a safety practice, but the previous package is **not a generic rollback mechanism after the database commit point**.

Before commit, the previous package can be reopened only when the canonical DB still has a lineage it recognizes.

After commit, an older package must independently run the same schema compatibility preflight. If the canonical database is newer than that older application, it must fail closed before mutation. The UI/help must never tell the user that opening the previous package automatically downgrades the database.

## Downgrade behavior

D4 distinguishes application downgrade from schema downgrade.

- D4 implements no schema downgrade migrations.
- Opening an older application does not automatically restore an older schema.
- An older application that sees a newer migration lineage refuses before mutation.
- Using an older package is safe only while the canonical database remains compatible with that package.
- No hidden SemVer downgrade policy is introduced in D4-A. If future application-version downgrade rules beyond schema compatibility are wanted, they need an explicit decision and tests.

## Domain-model clarification

This ADR supersedes only the **D4 persistence/authority interpretation** of the conceptual `AppSettings`, `BackupRecord` and `UpdateLog` sections in `docs/domain-model.md`:

- conceptual `app_version` is not a mutable AppSettings authority;
- conceptual `schema_version` is not a second numeric schema authority;
- automatic `before_migration` backup identity does not require creation of a new `BackupRecord` row;
- `UpdateLog` durable truth is external launcher/startup metadata so it survives migration failure;
- `backup_id` is therefore interpreted as a safe retained backup artifact identity for D4 rather than a required database foreign key;
- `rolled_back` is reserved unless a real rollback transition exists.

`docs/domain-model-d4-update-safety.md` is the bounded companion clarification for those conceptual fields. All unrelated domain-model semantics remain unchanged.

## Implementation slices

### D4-A — Version identity and compatibility preflight

**AUTHORIZED NEXT — NOT IMPLEMENTED**.

Scope:

- introduce one canonical repository-owned app-version source;
- derive package metadata/runtime projections from it;
- feed the same effective version into backend read-only status;
- reuse/generalize read-only migration-lineage classification for ordinary startup;
- fail closed on newer/unsupported/unreadable existing lineage before mutation;
- preserve first-run behavior only when the canonical DB file does not exist;
- focused backend/launcher/package tests.

D4-A does **not** redesign migration execution, implement UpdateLog, or add frontend update presentation.

### D4-B — Safe migration execution and durable UpdateLog

**PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED**.

Will own consistent staging snapshot, staged migration, backup verification, commit publication, interruption reconciliation and durable UpdateLog.

### D4-C — User-facing update status and packaged failure UX

**PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED**.

Will own read-only human status and fixed packaged update-failure UX.

### D4-D — Exact-package update verification and lifecycle closure

**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.

Will verify exact packaged manual-update scenarios and close D4 only after the previous slices are merged and independently verified.

## Explicit authorization boundary

CR-013 authorizes D4 as an accepted architecture programme and authorizes **only D4-A** as the next runtime implementation slice.

It does not authorize D4-B, D4-C, D4-D, D5 or distribution/release work.

## Considered alternatives

### 1. Direct in-place migrations with backup only

Rejected for D4. A backup is valuable recovery evidence but does not prove that a failed/ interrupted migration leaves the canonical working DB unmodified.

### 2. Second numeric schema-version field

Rejected. It duplicates and can diverge from the ordered `schema_migrations` lineage.

### 3. Database-only UpdateLog

Rejected as the sole durable truth. The database may be unavailable or untrusted precisely when the update failure needs to be recorded.

### 4. Reuse Restore as the update mechanism

Rejected. Restore is lifecycle-closed and has different source-selection, destructive-authority and recovery semantics.

### 5. Staged migration before atomic commit

Accepted. It proves the old canonical database remains authoritative until a complete migrated target has passed verification.

### 6. Auto-updater/download mechanism

Rejected from D4 scope. Delivery, download, release channels, internet update checking and installer infrastructure are separate product/release decisions.

## Rejected alternatives

D4 explicitly rejects:

- raw SQLite file copy for backup or migration stage;
- mutable database app-version authority;
- independently mutable numeric schema-version authority;
- in-place migration as the selected D4 safety design;
- DB-only UpdateLog as the sole durable log;
- browser-controlled update/migration paths;
- Restore-as-update;
- automatic schema downgrade;
- previous-package-as-guaranteed-rollback after commit;
- silent automatic destructive retry after interruption.

## Consequences

Positive:

- an older application fails closed before touching a newer database;
- migration failure before commit leaves the previous canonical DB authoritative;
- UpdateLog survives the database failure it describes;
- the package remains replaceable while user data remains external;
- the user gets bounded truthful status without a technical admin UI;
- no internet dependency is introduced.

Costs:

- D4-B needs careful staging ownership, atomic publication and interruption tests;
- update status and runtime-start status become two related but distinct state machines;
- disk space must temporarily accommodate the working DB, safety backup and migration stage;
- exact-package interruption verification is required before D4 closure.

## Test contract

### Decision PR

This changeset is documentation/state/lifecycle-checker only. Required checks:

1. `git diff --check`;
2. `python3 -m py_compile scripts/check_documentation_lifecycle.py`;
3. `python3 scripts/check_documentation_lifecycle.py`;
4. no changes under `launcher/**`, `backend/**`, `frontend/src/**`, `macos_package/**`, `backend/app/migrations/**` or package/dependency build inputs;
5. all protected Restore production blobs remain byte-identical;
6. all previously protected history blobs remain byte-identical;
7. pre-CR-013 active lifecycle/state/checker surfaces are preserved byte-identically under `docs/history/d4-pre-decision/`;
8. lifecycle checker negative probes catch premature D4 completion, D4-B/C/D authorization, D5 authorization, release-readiness claims, release/distribution authorization and Restore reopening.

### D4-A implementation contract

D4-A later must test at minimum:

- one version source feeds development status and packaged projections;
- mutable DB `app.version` cannot become effective authority;
- absent canonical DB follows first-run path;
- current known lineage starts normally without migration;
- supported older known prefix is classified as update-required without performing the D4-B migration redesign;
- `schema-newer-than-application` refuses before mutation;
- unknown/reordered/skipped/duplicate/unreadable lineage refuses before mutation;
- refusal happens before `before_migration` backup, backend start and browser handoff;
- packaged runtime uses the same preflight semantics;
- Restore behavior and protected Restore blobs remain unchanged.

## Stop conditions

STOP and require a separate decision if implementation would require any of the following:

- changing the Restore twelve-phase state machine or closed Restore production boundary;
- adding a backend Restore endpoint or browser filesystem/update authority;
- creating a second startup/migration engine;
- introducing raw SQLite copy semantics;
- making app version database-authoritative;
- introducing an independently mutable schema-version counter;
- requiring cloud/network service for ordinary startup/update;
- requiring a new desktop shell;
- implementing auto-download, release channels, signing, notarization, DMG, App Store or D5 work;
- claiming product release readiness.

## Non-goals

CR-013 and this ADR do **not** authorize or implement:

- auto-update download or internet update checking;
- GitHub Releases integration;
- release channels or background updater;
- installer redesign;
- signing or notarization;
- DMG;
- App Store;
- sandbox migration;
- cloud sync/deployment;
- multi-user/roles;
- D5;
- release-candidate certification;
- Electron, Tauri, pywebview or another desktop shell;
- new Restore semantics, transport, endpoint or browser filesystem authority;
- terminal-based user update workflow.
