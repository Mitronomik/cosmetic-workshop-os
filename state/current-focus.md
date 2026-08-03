# Current focus — C3 closed, merged, exact-head verified and hardened; C4 Restore decided as launcher-assisted

Active phase: **Roadmap completion window — C1 complete; C2 complete; C3 `COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED` after PR #167 and PR #168; `CR-004`, `CR-006` and `CR-009` accepted and implemented; `CR-010` accepts launcher-assisted Restore; C4 has an accepted product decision and no implementation**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `R4 — Canonical backup/export filename reason normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED AND IMPLEMENTED**
- `CR-007 — C1 workshop tax-rate setting contract`: **ACCEPTED AND IMPLEMENTED**
- `C1-I — Implement backend-owned tax-rate setting`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #149)
- `CR-008 — C2 financial estimates and immutable production snapshots`: **ACCEPTED AND MERGED** (PR #150, merge commit `4c03142ef7acdc31fcb15730484e8e52dde95b69`)
- `C2-I — Backend financial readiness estimate`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #151)
- `C2-II — Transactional production financial snapshots`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #152)
- `C2-III-A — Order and ProductionBatch financial presentation`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #154)
- `C2-III-B — Snapshot-backed reports and report documents`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #157)
- `C2 — COMPLETED`
- `C3-I — Read-only AuditLog workspace`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #159)
- `C3-II-A — Atomic workshop-profile AuditLog coverage`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #161)
- `CR-009 — Durable file-backed artifact AuditLog semantics`: **ACCEPTED**
- `C3-II-B1 — Durable ledger and report-document AuditLog coverage`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #163)
- `CR-006 — JSON export create-response confirmation semantics`: **ACCEPTED — PRODUCT DEFECT CONFIRMED AND CONTRACT DECIDED**
- `C3-II-B2 — JSON export AuditLog coverage`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #166)
- `CR-004 — SQLite backup transaction consistency`: **ACCEPTED — PRODUCT DEFECT — BACKUP CONSISTENCY (HIGH)**
- `C3-II-B3 — Manual backup AuditLog coverage`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #167, merge commit `7af53a3305fa9fdb984d4c478e1186685fbb6727`, final reviewed head `259697805660fd4dc37e6ac5f50567d48037be94`)
- `CR-004 — SQLite backup transaction consistency`: **ACCEPTED AND IMPLEMENTED**
- `C3 artifact-finalization hardening`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #168, final reviewed head `6c57c7f5ba851ce2124577268baeda07d19ce4ae`, merge commit `867afeb0967637d07172f88c95e02e9bc500a311`, merged `2026-08-02T08:34:02Z`)
- `C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED`
- `CR-010 — Launcher-assisted Restore semantics`: **ACCEPTED**
- `C4-I — Launcher-owned restore safety engine`: **IMPLEMENTED ON PR BRANCH — FOURTH CORRECTION APPLIED — NOT MERGED**
- `C4-II — User-facing launcher Restore flow`: **PLANNED — NOT AUTHORIZED**
- `C4-III — Restore end-to-end verification and lifecycle closure`: **PLANNED — NOT AUTHORIZED**
- `C4 — ACTIVE`
- `C4 product decision — COMPLETE`
- `Restore — NOT IMPLEMENTED`
- `Product release readiness — NOT CLAIMED`
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **PR #168 is merged.** The artifact-finalization hardening is on merged `main`, not on a branch, so C3 is complete **and hardened**.

## Current next action

```text
C4-I — Launcher-owned restore safety engine
IMPLEMENTED ON PR BRANCH — FOURTH CORRECTION APPLIED — NOT MERGED
```

**Next action: an independent audit of the new published head of PR #170.** The
branch is `codex/c4-i-launcher-restore-safety-engine`, started from `origin/main`
at `b89cbaaaf41a56c810847d7c1e593712c5591eb6` (the PR #169 merge commit). The PR
stays **draft** until that audit clears it. Nothing else is authorized.

**Four independent audits have run, finding twenty findings in total — 5 + 5 + 7
+ 3 — each round against the correction the previous round produced. All twenty
are closed.** The first found five safety-critical gaps in the original
implementation:

```text
P1-1  source WAL/journal sidecars are checked beside the ORIGINAL selected
      source, before and after the copy, and staging reads a held descriptor
      whose identity is re-proved
P1-2  backend shutdown is proved by owning the exact process handle, never by a
      free port and never by pattern-killing
P1-3  every destructive path is derived from the launcher's own resolvers; a
      caller supplies only the selected source
P1-4  a failed `rollback_in_progress` publication attempts no unauthorized
      transition and reports the phase actually on disk
P1-5  parent-directory durability is mandatory, and a post-rename failure is
      classified rather than swallowed
```

A second audit of that correction found five more, all closed as well:

```text
P1-1  a post-rename failure publishing `completed` fell through to the abort
      path and attempted `completed → aborted`, an edge the graph forbids
P1-2  ordinary startup was permitted by a negative rule, so unresolved
      pre-replacement phases were treated as safe; the initial `prepared`
      publication could also be reported as "no record"
P1-3  a same-size in-place rewrite of the selected source kept device, inode,
      size and type identical and escaped the identity checks
P2-1  a hard launcher crash lost the in-memory process handle, so an orphaned
      backend appeared absent
P2-2  the `F_FULLFSYNC` fallback was documented as "recorded" but was not
```

A third audit of that second correction found seven more, all closed as well:

```text
P1-1  the backend-liveness lock was checked momentarily and released, which
      proves availability at an instant and reserves nothing — a backend could
      start during journal settlement or the replacement itself. It is now a
      retained launcher maintenance lease, required by
      `require_backend_stopped()`, held through the safety copy, journal
      settlement, replacement, rollback replacement and post-replacement
      verification, and released only for an owned backend that must run.
      The lock was also taken too late: a launcher-managed child now acquires
      it in `app.launcher_backend_entrypoint` **before importing any
      application module** and proves that acquisition to the launcher over a
      bounded one-run pipe-and-token handshake.
P1-2  an orphaned backend made `RestoreLifecycleError` escape startup
      recovery, where `run_local_runtime` expects a `RecoveryResult`. Startup
      recovery now returns a typed blocked result — nothing starts, the browser
      stays closed, nothing on disk changes, and the user sees one sentence
      rather than a traceback.
P1-3  an ambiguous initial `prepared` publication re-read `operation.json`
      without checking whose record it is, so a previous operation's terminal
      record could be reported as this attempt's outcome and identity. The
      operation ID is compared first; a foreign record is never inherited and
      never modified.
P1-4  `RestoreOperationStateStore.create()` treated all four terminal phases as
      replaceable, including `recovery_blocked` — the authoritative pointer to
      an unresolved operation and the evidence it names. Only the positive
      `SAFE_TERMINAL_STARTUP_PHASES` vocabulary is replaceable now.
P2-1  a visible-but-unconfirmed `completed` used the rollback sentence,
      claiming a rollback that did not happen and a return to previous data
      that are not authoritative. One fixed
      `COMPLETION_DURABILITY_UNCONFIRMED` category says only what is known.
P2-2  the PR body still described the previous head, test counts and smoke.
P2-3  one pre-correction test node ID had been renamed rather than preserved.
```

A fourth audit of that third correction found three more, all closed as well:

```text
P1-1  the maintenance lease was released around the entire startup-plus-
      two-cycle verification block rather than around each exact owned-backend
      lifetime. That left two windows with nothing holding the canonical lock:
      startup migrations, which need no backend at all, and the gap between the
      two verification cycles, where cycle 1's child had exited and the launcher
      had not taken the lease back. Startup and migrations now run under the
      retained lease, and each cycle is its own release/handshake/stop/reacquire
      window, so the lease is held before cycle 1, between the cycles and after
      cycle 2. `owned_backend_window()` refuses to open without the lease, and
      the verifier is given `run_backend_cycle` as a required keyword-only
      parameter, so "release once, start twice" cannot be expressed.
P1-2  `run_local_runtime()` checked the port before Restore recovery. A real
      orphan is a running backend and holds the canonical liveness lock *and*
      the configured port, so the port check fired first and raised
      `RuntimeLaunchError` about a busy port — a traceback and the wrong story —
      while the typed blocked `RecoveryResult` never ran. Recovery and backend
      liveness are now resolved first; the port check keeps its own unchanged
      message for the ordinary collision, and an occupied port is never
      reinterpreted as a Restore problem.
P2-1  the PR body carried inconsistent finding counts and did not describe this
      correction. The accounting is now twenty findings across four independent
      audits, 5 + 5 + 7 + 3.
```

No audit required a change to the accepted twelve-phase machine, and no
condition any of them found justified a new phase.

`C4-I` implements the accepted `CR-010` state machine exactly — the same twelve
phases, transition graph, recovery matrix and `replacement_intent` crash rule — so
no amending decision was required. It is internal launcher infrastructure only:
`launcher/restore/` plus one bounded read-only backend helper
(`backend/app/db/migration_lineage.py`), with **no** API endpoint, route, button,
dialog, file picker, product terminal workflow, migration, schema change,
AuditLog event or frontend change. No PR-specific smoke runner is committed —
the smoke-authoring contract requires it to live outside the code it verifies, so
the `C4-I` runner is created outside the repository and drives a detached checkout
of the exact published head. Implementation detail:
`docs/backup-and-restore.md` § 16.

`C4-II` and `C4-III` stay `PLANNED — NOT AUTHORIZED` and must not be started from
this branch. **Restore remains `NOT IMPLEMENTED`** — the engine has no user-facing
entry point. macOS packaging, the safe packaged update flow and the full
release-candidate smoke remain **not completed**; product release readiness is
**not claimed**.

## C3 closed and hardened; C4 Restore decided (2026-08-02)

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-004 — ACCEPTED AND IMPLEMENTED
CR-006 — ACCEPTED AND IMPLEMENTED
CR-009 — ACCEPTED AND IMPLEMENTED
C3 artifact-finalization hardening — DONE — MERGED AND EXACT-HEAD VERIFIED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED — NOT IMPLEMENTED
C4-I — AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
C4-II — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
C4 — ACTIVE
C4 product decision — COMPLETE
C4 implementation — NOT STARTED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR #168 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #168 — `C3 hardening — Separate artifact verification from AuditLog persistence` |
| State | `MERGED`, base `main`, non-draft |
| Head branch | `claude/c3-hardening-artifact-finalization` |
| Final reviewed head | `6c57c7f5ba851ce2124577268baeda07d19ce4ae` |
| Merge commit | `867afeb0967637d07172f88c95e02e9bc500a311` |
| Merged at | `2026-08-02T08:34:02Z` |

The final reviewed head is an ancestor of the merge commit, and the merge commit
is an ancestor of `origin/main`.

**Accepted merged PR #168 evidence.** None of these results was executed in this
documentation pull request.

| Check | Accepted result |
|---|---|
| Complete backend | `1826 passed` |
| Complete root suite | `1843 passed` |
| Launcher | `17 passed` |
| Baseline node IDs | `1804` preserved / `0` lost / `39` added |
| Frontend | all `21` `test:*` scripts passed |
| Frontend production build | `PASS` |
| `frontend/src/main.ts` | `6399` lines |
| Final independent audit | `P0 — none`, `P1 — none`, `P2 — documented only` |
| Exact-head launcher/API/browser smoke | `PASS` |

**Accepted hardened behaviour on merged `main`.** Report-document and JSON-export
finalization use typed, artifact-specific results. `recorded` means the artifact
was verified and its AuditLog event committed. `audit_pending` means the artifact
was verified but AuditLog persistence did not commit. `artifact_invalid` means
mandatory verification did not prove the artifact authoritative. Only `recorded`
and `audit_pending` may produce HTTP `201`; `artifact_invalid` produces a fixed
structured HTTP `500`. An invalid artifact is not deleted, is not audited,
remains unresolved and is counted for bounded reconciliation. Filenames, paths,
reasons, operation IDs, schema versions, entity counts, verifier details and
SQLite details are not exposed through safe error responses.

`CR-004`, `CR-006` and `CR-009` and their accepted decisions are **not reopened**.

**`CR-010 — Decide launcher-assisted Restore semantics` is accepted.** MVP
Restore is launcher-assisted: Restore is not performed by a running FastAPI
backend endpoint and is not an ordinary SPA mutation, and the launcher owns
process shutdown, backup validation, the pre-restore safety copy, staging,
atomic database replacement, post-restore startup verification, rollback and
incomplete-restore recovery. Support-assisted recovery stays a fallback for
failures that cannot be resolved automatically. The user never needs Git,
Python, Node.js, Docker, SQLite tools, GitHub or a terminal. Durable decision:
`docs/decisions/0016-launcher-assisted-restore.md`; complete contract:
`docs/backup-and-restore.md`.

### The accepted Restore phase machine — C4-I must implement it exactly

`CR-010` decides the durable crash-recovery state machine so that `C4-I` does not
invent a safety-critical one as an undocumented implementation decision. The
launcher-owned operation record carries **exactly one authoritative field,
`phase`**, and it is mutually exclusive. Whether replacement occurred and whether
rollback completed are **derived** from it, never persisted as independent
authoritative fields that could contradict it.

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

No alias, no prose-only synonym, no thirteenth phase. Allowed transitions:

```text
prepared → source_staged → candidate_validated → safety_copy_verified
→ replacement_intent → replacement_committed → verification_in_progress
→ completed

prepared | source_staged | candidate_validated | safety_copy_verified
→ aborted

replacement_intent | replacement_committed | verification_in_progress
→ rollback_in_progress

rollback_in_progress → rolled_back
rollback_in_progress → recovery_blocked
```

Terminal phases are `completed`, `aborted`, `rolled_back` and
`recovery_blocked`. A new attempt is a new operation with a new operation ID; a
terminal record is never reactivated.

**Why `replacement_intent` exists.** Filesystem replacement and SQLite are not
one transaction, so the window `persist intent → atomic replacement → persist
committed` cannot be observed from outside after a crash. The launcher durably
records `replacement_intent` immediately **before** the replacement boundary,
and:

```text
A persisted replacement_intent is treated as though replacement may have
occurred, even when the current working file appears unchanged.
```

No timestamp, size, filename, inode, migration version or content check may be
used to guess otherwise — the staged candidate is by construction a valid
workspace database. The safe outcome is rollback from the verified safety copy.

**Ordering and gates.** Every transition is persisted through one documented,
tested, atomic publication boundary before the next action that depends on it;
an in-place truncate-and-rewrite of the only record is insufficient.
`replacement_intent`, `replacement_committed` and `verification_in_progress` all
block ordinary startup and all recover through rollback. `rolled_back` is a
**failed** Restore, never success. `recovery_blocked` never permits ordinary
startup. **The ordinary browser opens only after `completed` has been durably
recorded.**

Every persisted phase has exactly one required startup behaviour, fixed by the
recovery matrix in `docs/decisions/0016-launcher-assisted-restore.md` § 7.5 and
`docs/backup-and-restore.md` § 7.4. `C4-I` implements that matrix exactly and may
not substitute an alternative state machine.

**Working-database mutation boundary.** The staged candidate must pass the
complete validation contract before any mutation, replacement, deletion or
migration of the current **working database**. Creating the isolated operation
directory, the narrow durable operation record, launcher-owned staging files and
local technical logs is Restore infrastructure and is not such a mutation. The
user-selected source stays immutable.

All four accepted backend baseline gate failures are closed on `main`. The accepted `CR-007` decision (PR #148, merge commit `80b83de3e838cf676669a1b627770300590c99c0`, final reviewed head `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`) authorized exactly one bounded implementation slice, and that slice is now merged.

## HISTORICAL — PARTIALLY SUPERSEDED — C3 hardening follow-up while its PR was open

> **What the hardening does is unchanged and is the merged behaviour.** Only its
> lifecycle statements are superseded: its `IMPLEMENTED ON PR BRANCH — NOT
> MERGED` status line and its instruction that *"C4 must not be activated until
> this follow-up merges"* were true while PR #168 was open. PR #168 is now
> **merged** at `867afeb0967637d07172f88c95e02e9bc500a311`, so C3 is complete and
> hardened and that C4 gate is satisfied.

```text
C3 hardening follow-up:
separate artifact verification failure from AuditLog persistence failure for
report documents and JSON exports.
```

`C3-II-B3` corrected this for manual backups: `finalize()` returns a typed
`BackupFinalization` with `recorded`, `audit_pending` and `artifact_invalid`, so
an artifact that fails mandatory verification can never be reported as a created
artifact with a merely pending Journal entry.

`report_document_audit.py` and `export_audit.py` returned `int | None`, and
their create paths mapped every `None` to `201` with `audit_status: pending`.
They therefore carried **the same defect class** that was classified blocking
for backups: a report document or JSON export that failed verification was
reported to the user as successfully created.

This was deliberately kept out of PR #167 — correcting two merged, separately
accepted slices there would have been an unrelated refactor across a diff whose
subject is backups — and it was run as the immediate follow-up instead.

**Status at the time of writing (HISTORICAL): `IMPLEMENTED ON PR BRANCH — NOT
MERGED`** on `claude/c3-hardening-artifact-finalization`. It is now
`DONE — MERGED AND EXACT-HEAD VERIFIED` as PR #168.

The defect was reproduced against merged `main` before any correction, in ten
cases across both artifact kinds, including two genuine (non-injected) verifier
verdicts: a report-document size mismatch and an unreadable export. Every case
returned `201` with `audit_status: pending` and wrote no AuditLog event.

Both finalizers now return artifact-specific typed results —
`ReportDocumentFinalization` and `ExportFinalization` — carrying `recorded`,
`audit_pending` or `artifact_invalid`. Only `recorded` and `audit_pending` make
the artifact authoritative. `artifact_invalid` raises a dedicated fixed-contract
error (`report_document_verification_failed` / `export_verification_failed`)
that the API maps to a structured HTTP `500` with no filename, path, reason,
operation ID, schema version, entity count or SQLite detail. A verified artifact
whose Journal write failed still returns `201 pending`.

No migration, no second ledger, no outbox, no generic artifact framework, no
worker. Backup finalization is untouched. `CR-006` create-response behaviour is
unchanged.

**C4 must not be activated until this follow-up merges, or until it is
explicitly accepted as a known release blocker.** *(HISTORICAL — satisfied. The
follow-up merged as PR #168 on 2026-08-02, so this gate no longer blocks C4.)*

## HISTORICAL — PARTIALLY SUPERSEDED — CR-004 resolved; C3-II-B3 implemented on its PR branch (2026-08-02)

> The `CR-004` evidence and the delivered scope below stand. Its closing
> lifecycle sentence — *"C3 is complete on this branch and incomplete on merged
> `main`"* — is superseded: `C3-II-B3` merged as PR #167 and the hardening
> follow-up merged as PR #168, so C3 is complete and hardened on merged `main`.

`CR-004` is **accepted** and classified:

```text
CR-004 — PRODUCT DEFECT — BACKUP CONSISTENCY — HIGH
```

The evidence ran against merged `main` = `844526ae4057a454312f790abcaf21be518cdbd9`
with Python `3.12.10` and SQLite `3.49.1`, on isolated temporary user-data
directories with no real user data.

| Scenario | Result on the raw `shutil.copy2` path |
|---|---|
| Quiescent copy (control) | correct — 25/25 rows, `ok`/`ok`, source unchanged |
| WAL, committed uncheckpointed | **0 of 200** committed rows in the copy, `quick_check = ok` |
| Concurrent writers under WAL | 954 committed transactions, **0 rows** in all 10 snapshots |
| Rollback journal, transaction in flight | **12 of 12** copies held two transaction states, including rolled-back rows |
| Same, with the stock page cache | reproduced — not a harness artefact |
| Uncommitted spilled pages | `quick_check` **failed**; 506 committed rows missing, 465 never-committed exposed |
| Source mutation | **none observed**, either engine, any scenario |
| Plain `Connection.backup()` under a held lock | **never returned** |
| Aborted copy | 0-byte file that passes `quick_check` and is listed |
| Create-path directory re-list | HTTP `500` under all four injected faults, with a complete backup on disk |

The categories are kept distinct: the WAL findings are **omission of committed
data**, the rollback-journal findings are **mixed transaction state and
inclusion of never-committed data**, and **corruption** is claimed only for the
one scenario where a structural check actually failed. This is not live-data
loss — the source database is never modified — but the artifact whose only
purpose is recovery could be silently incomplete.

Delivered on the branch: the SQLite Online Backup API engine with a single
whole-database step and bounded busy behaviour; one strict generated-filename
grammar proved by a byte-for-byte round trip; exact filename reservation guarded
by active-ledger identity; a `prepared` `manual_backup` ledger row committed
before the snapshot; exact artifact verification including the embedded
operation row; exactly-once `backup.created` finalization; startup and bounded
pre-create reconciliation; additive `audit_status` / `audit_message` and
`pending_audit_count`; a create response built from the exact `BackupResult`
with no directory re-list; `frontend/src/backup-audit-contract.ts`; and the
backend-owned Journal vocabulary `Резервная копия создана` / `Резервная копия`.

The load-bearing property is the **embedded prepared operation**. A backup is
itself a SQLite database, so unlike a document or an export it can prove which
operation produced it — and it must, because an unrelated but perfectly healthy
database placed at the reserved path passes every structural check, and an empty
file returns `quick_check = ok`. The completed backup is never rewritten
afterwards to promote that row to `audited`.

No migration was added and `0020` is unchanged. The automatic `before_migration`
backup keeps using the same safe engine, stays before migrations, creates no
ledger row and is never audited.

`C3-II-B3` is the **last remaining C3 slice**, so C3 is complete on this branch
and incomplete on merged `main`. C4 stays inactive, Restore stays unimplemented,
and product release readiness is not claimed.

## HISTORICAL — PARTIALLY SUPERSEDED — C3-II-B1 merged and exact-head verified (2026-08-01)

> The PR #163 closure facts and evidence below stand. The surrounding lifecycle
> block is **superseded**: `C3-II-B3` has since merged as PR #167, the
> artifact-finalization hardening merged as PR #168, and C3 is
> `COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED`.

```text
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-006 — ACCEPTED — PRODUCT DEFECT CONFIRMED AND CONTRACT DECIDED
C3-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-004 — ACCEPTED — PRODUCT DEFECT — BACKUP CONSISTENCY (HIGH)
C3-II-B3 — IMPLEMENTED ON PR BRANCH — NOT MERGED
C3 — INCOMPLETE ON MERGED MAIN — COMPLETE ON THE B3 BRANCH
C4 — INACTIVE
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR #163 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #163 — `C3-II-B1 — Durable ledger and report-document AuditLog coverage` |
| State | `MERGED`, base `main`, non-draft |
| Head branch | `claude/c3-ii-b1-report-document-audit` |
| Final reviewed head | `afd65fd2878fa02a0d4dc4963812c80644a4e787` |
| Merge commit | `ef0297e41a731f082a2a21a46b361aa9aac36cfa` |
| Merged at | `2026-08-01T05:30:38Z` |
| Merged implementation state | `DONE` |
| Final exact-head result | `PASS` |

The final reviewed head is an ancestor of the merge commit, and the merge
commit is an ancestor of `origin/main`. The branch was based on verified
`origin/main` = `385873fa9f393f9dc4dcac14e7bc79e0da12c5d1` (PR #162 merge
commit).

**Accepted merged PR #163 evidence.** None of these results was executed in
the documentation task that recorded this closure.

| Check | Accepted result |
|---|---|
| Complete backend + launcher suite | `1550 passed / 0 failed` |
| Backend collection | `1533` |
| Original backend baseline node IDs | all `1376` preserved / `0` missing |
| Added backend tests | `157` |
| Complete launcher suite | `17 passed / 0 failed` |
| Frontend | all `19` `test:*` scripts passed |
| Frontend build | `PASS` |
| Final exact-head launcher smoke | `PASS` on `afd65fd2878fa02a0d4dc4963812c80644a4e787` |

The final exact-head audit found:

```text
P0 — none
P1 — none remaining
P2 — documented and non-blocking
```

The single P1 the audit found — the broad `except Exception` on the create-path
identity reservation — was fixed in the final head `afd65fd`. The recorded P2
items are the verifier's local copy of the format vocabulary (pinned by a test),
`_unique_document_paths` being bounded by ledger contents rather than an explicit
cap, and the finalizer's rollback signal overloading `RuntimeError`. The focused
exact-head launcher smoke is **not** release smoke.

Delivered on merged `main`: migration `0020_artifact_audit_operations` registered once after
`0019`; the bounded ledger repository and its pure domain vocabulary; the
shared report-document pair verifier; the idempotent write-serialized
finalizer; startup reconciliation after migrations; one pre-create
reconciliation pass; additive `audit_status` / `audit_message` create fields
and `pending_audit_count` status field; the backend-owned safe Journal
vocabulary for `report_document.created`; and the frontend
success-plus-separate-warning presentation.

`AuditLogRepository.create_log(...)` now returns `cursor.lastrowid` as `int`.
Every existing parameter, the optional caller-owned connection and the insert
itself are unchanged, and existing callers that ignore the value are
unaffected.

Only `report_document` has a runtime writer. `json_export` and `manual_backup`
exist solely in the table's `CHECK` vocabulary so B2 and B3 need no second
migration.

**Two issues found in review of the first PR head, both corrected on the branch:**

1. `launcher/runtime.py::start_backend_process` passed only `PYTHONPATH` to the
   uvicorn child, so the API resolved `get_database_config()` on its own and
   could fall back to `DEFAULT_DATABASE_PATH` while `initialize_startup` had
   backed up, migrated and reconciled `<user_data>/data/cosmetic_workshop.sqlite`.
   Startup and the API could therefore use different databases.

   `run_local_runtime` now passes `startup.database_path` explicitly, and
   `start_backend_process` writes it to `COSMETIC_WORKSHOP_DB_PATH`, overriding
   any stale inherited value. The key is read from the backend's own
   `DATABASE_PATH_ENV` rather than duplicated as a literal. This applies to
   development mode as well.
   `launcher/tests/test_runtime_database_continuity.py` proves the continuity
   through the database itself — migration `0020`, the ledger row and the
   AuditLog event all land in the startup-selected file, the repository default
   stays untouched, and a restart reconciles that same database.

   `start_backend_process()` takes `database_path: Path` as a **required**
   parameter and pins the environment unconditionally, so no future caller can
   quietly reintroduce the split; omitting it is a `TypeError` at the call site.

2. `ReportDocumentAuditService.pending_count()` degraded to `0` when the ledger
   could not be read. That was untruthful: `0` is a claim that nothing is
   awaiting a Journal entry, and the frontend clears a standing warning on it.
   The fallback is removed; a read failure now surfaces through the existing
   service/API error boundary as a fixed Russian message with no SQLite detail,
   and the status endpoint stays read-only. The caught tuple is narrowed to
   `(sqlite3.Error, OSError)` — the failures the persistence boundary genuinely
   produces — so an unexpected programming defect propagates as itself instead
   of being dressed up as a known availability problem.

`launcher/tests/test_runtime.py::test_launcher_startup_respects_user_data_override`
was failing on the untouched baseline `385873f` because its local
`ALLOWED_TABLES` copy was frozen near the `0011` schema. It now uses the shared
`app.tests.table_guards`, so it tracks the real migration head and stays a
bounded check. The complete launcher suite is green.

**Hardening and independent audit of the published branch:**

`ReportDocumentService.status()` and the create path's identity reservation both
caught `except Exception`, which would have reported a programming defect to the
user as a specific, recoverable condition it is not. Both are narrowed to
`(sqlite3.Error, OSError)` — what the persistence boundary genuinely raises —
and both run where letting an unexpected error propagate costs nothing, because
no artifact exists yet at that point.

Two broad catches are deliberately **kept**, and documented in place: the
metadata-validation catch inside `verify()` and the `RuntimeError` catch in
`finalize()`. Both guard the path *after* both files exist, where the accepted
contract requires HTTP `201` with `audit_status: pending`. Narrowing them would
let an unexpected error escape and turn a completed document into a false total
failure — the exact outcome CR-009 forbids.

`start_backend_process()` now requires `database_path: Path` with no default and
sets the environment unconditionally, so the startup/API database split cannot
be reintroduced by a future caller; omitting it is a `TypeError` at the call.

The finalizer's exactly-once guarantee was re-verified independently under
12-way concurrent finalization and under racing finalize/reconcile, and seven
mutation checks (false-zero fallback, loose audit contract, count coercion,
removed write serialization, removed in-transaction re-read, primary-only
identity check, abandoning ambiguous pairs) were each confirmed to fail the
suite.

## HISTORICAL — SUPERSEDED — what was authorized next at the CR-006 decision (C3-II-B2 only)

> Superseded by § *What is authorized next* at the top of this file. `C3-II-B2`
> merged as PR #166 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`.

```text
C3-II-B2 — IMPLEMENTED ON PR BRANCH — NOT MERGED
```

Next active work: **`C3-II-B2` — one bounded JSON export AuditLog
implementation pull request**, begun only after the `CR-006` decision pull
request is merged and only from `origin/main`.

Explicit boundary:

```text
One bounded implementation PR.
Reuse the existing artifact_audit_operations ledger.
No new migration.
No manual-backup coverage.
No CR-004 resolution.
```

`C3-II-B2` scope, the exact export verification contract, the future create and
status response contract, the AuditLog privacy contract and the non-goals are in
`docs/implementation-plan.md` § *C3-II-B2 — JSON export AuditLog coverage*, with
the reserved event vocabulary in `docs/decisions/0013-file-backed-artifact-audit-semantics.md`
§ *Audit privacy and vocabulary* and the create-response contract in
`docs/decisions/0014-json-export-create-confirmation-semantics.md`.

`C3-II-B2` also carries the accepted `CR-006` create-response correction, so the
export create path is touched exactly once: the create response is built from
the creator's exact `ExportResult`, its `reason` is parsed from the exact final
filename through the same contract list and status use, and the directory-wide
re-scan leaves the create path.

`CR-004` remains `needs evidence` and unresolved, so `C3-II-B3` stays blocked.

## C3-II-A closure and CR-009 decision

PR #161 is `MERGED`, base `main`, final reviewed and smoke-tested head
`6c327630d0e4cca3c566253bf9f8224aaaa33172`, merge commit
`3fec160f08aa7e775aa3e7ea650e570bf48955ad`, merged
`2026-07-30T08:11:41Z`. Exact-final-head evidence is
`PASS — EXACT-HEAD C3-II-A FOCUSED SMOKE PASSED`.

Focused backend `591 passed / 0 failed / 0 skipped`, complete backend
`1376 collected / 1376 passed / 0 failed / 0 skipped`, all `1364` baseline
node IDs preserved with `12` added, all `18` frontend `test:*` scripts,
focused AuditLog frontend `92 passed`, timezone-focused AuditLog frontend
`92 passed`, and frontend build `PASS` were executed on
`354104cc326f1e1374324ef9128e5ef771a4a063`. The final documentation-only
head was production/test byte-identical. Those suites were not rerun on the
final head and are not exact-final-head runs; the exact-head focused smoke is
not release smoke.

`CR-009` accepts the durable contract in
`docs/decisions/0013-file-backed-artifact-audit-semantics.md`. A verified
manual backup, JSON export or report document is the authoritative primary
result. Audit finalization failure preserves it and returns HTTP `201` with
`audit_status: pending` plus a separate Russian warning. One bounded
`artifact_audit_operations` ledger prepares the operation before the file
write, and exactly one AuditLog row plus the transition to `audited` commit
together by stable unique `operation_id`.

Reconciliation runs only after migrations during normal startup and before
another scoped create. It inspects only recorded safe relative filenames under
the expected artifact directory and uses the same idempotent finalizer.
GET/list/status endpoints never reconcile; there is no background thread,
unbounded retry, directory scan or legacy backfill. Paths, filenames, reasons,
contents, Workshop profile, entity counts, client data and arbitrary text are
excluded from AuditLog.

The ledger filename fields are internal reconciliation identities, not
AuditLog content. Report-document filenames contain no request reason; future
B2/B3 primary filenames may contain the canonical filename-derived reason
segment accepted by CR-005. There is no separate reason column and no raw
human/request/export-manifest reason or other separate user-authored text.
CR-005 is not reopened, and existing artifacts are not renamed or rewritten.
The automatic `before_migration` backup stays outside CR-009 and before
migrations.

> **Decision-time authorization text — superseded by the current lifecycle
> above.** The paragraph below records the boundary CR-009 set when it was
> accepted, and it is the boundary the merged B1 slice was held to. B1 is now
> `DONE — MERGED AND EXACT-HEAD VERIFIED` through PR #163; it must not be read
> as open work.

Only C3-II-B1 is authorized after this documentation PR merges. B1 is limited
to the next sequential ledger migration, bounded ledger/finalizer, startup and
report-document pre-create reconciliation, report-document integration,
`report_document.created`, additive create fields `audit_status` /
`audit_message`, additive status field `pending_audit_count`, frontend
success-plus-warning presentation, tests and focused exact-head smoke. B2
remains blocked by CR-006; B3 remains blocked by CR-004. No runtime PR number is
assigned.

B1 preparation failure has the exact documented HTTP `500` safe detail and
creates no files, audit or ledger row. Its pending warning names only next
startup and next document creation. `pending_audit_count` counts
`report_document` rows in `prepared`/`pending_audit` and excludes
`audited`/`abandoned`; the status GET only reads it. Finalization uses one
caller-owned write-serialized connection, a compatible
`AuditLogRepository.create_log(...) -> int` extension, and commits the AuditLog
insert plus audited ledger state together or neither. The exact document-pair
verification and reconciliation failure rules are binding in ADR 0013 and
`docs/report-documents.md`.

## C1-I — merged, verified, DONE

`C1-I` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #149 `C1-I — Implement backend-owned tax-rate setting`, state `MERGED`
- Final reviewed head: `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`
- Merge commit: `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`
- Merged at: `2026-07-27T19:44:53Z`
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

Accepted merged evidence. None of these results was executed in the documentation task that recorded this closure.

| Check | Accepted result |
|---|---|
| Backend complete suite | `671 collected, 671 passed, 0 failed, 0 skipped` |
| Original merged baseline node IDs still collected | all `562` |
| Focused tax-setting frontend suite | `52 passed, 0 failed, 0 skipped` |
| All 13 focused frontend suites | `568 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Exact-head `/settings` browser smoke | `PASS — 146 checks / 0 failures` |
| Exact smoke-tested head | `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` |
| `frontend/src/main.ts` | `6406` before → `6399` after |

Delivered on merged `main`: `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate` in a dedicated router, service, schema, and domain-validation module under the existing `/api/settings` namespace; persistence of the key `default_tax_rate` through the existing `app_settings` table with **no migration**; strict decimal-string validation with structured Russian errors; the canonical exactly-two-decimal representation; a backend-generated monotonic `effective_at`; explicit Clear as row deletion of the `default_tax_rate` row only; exactly one atomic `tax_rate_setting_changed` audit per real mutation with rollback on audit failure; the no-op contract; the `Налоговая ставка для расчётов` section inside `/settings`; and the Settings Decision Matrix marking `default_tax_rate` — and only `default_tax_rate` — as newly editable. The legacy `tax.default_rate = "0.06"` placeholder is unchanged and is never read as a configured rate.

`C1-I` implemented **only the tax-rate setting**, not any C2 calculation. It no longer awaits smoke, review, or merge, and it is not reopened.

## CR-008 — accepted C2 financial decision

`CR-008 — Decide C2 financial estimates and immutable production snapshots` is **accepted** (RECORDED PRODUCT-OWNER DECISION, 2026-07-27) and **not implemented**. The durable contract is `docs/decisions/0012-c2-financial-calculation-snapshots.md`, with the formulas in `AGENTS.md` § 6.6, `docs/architecture.md` § 8.6, and `docs/domain-model.md`, the API mapping in `docs/api.md`, the report boundary in `docs/reports.md`, and the slice contracts in `docs/implementation-plan.md` § 11.

- **Product boundary.** An internal operational estimate for the workshop — never tax filing, a declaration, VAT accounting, automatic regime selection, УСН / ОСНО / НПД / ПСН / АУСН / ЕСХН calculation, insurance contributions, minimum tax, annual or quarterly tax accounting, marketplace tax accounting, invoicing, bookkeeping, or legal or tax advice. Nothing is renamed to a tax reserve. The simplified percentage-of-sale model is the accepted MVP model and may be replaced only by a separately decided future tax-regime model, after which existing snapshots stay immutable.
- **Formulas.** `Decimal` only, never binary float: `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent / 100)`; `margin = ROUND_MONEY(sale_price − total_cost − tax_amount)`; `margin_percent = ROUND_PERCENT(margin / sale_price × 100)`. The percentage is always divided by `100`; money and percentage quanta are both `0.01` with `ROUND_HALF_UP`; only the final amount of each formula is rounded; tax is deducted from gross revenue, never added on top.
- **Availability.** Configured `0.00` yields tax `0.00`. A missing rate or missing sale price yields `null`, never a fabricated zero. Margin is `null` when sale price, total cost, or tax is unavailable. Margin percent needs an available margin **and** a sale price greater than zero; a zero sale price yields `partial` with margin percent `null` and the warning `margin_percent_unavailable_zero_sale_price`. Negative margin and negative margin percent are valid and are never clamped. An invalid persisted rate is handled defensively with `tax_rate_invalid`, without coercion, without a fabricated zero, and without an unhandled HTTP 500.
- **No valid configured tax-rate context.** A missing `default_tax_rate` row and an invalid persisted value stay distinguishable through the warnings `tax_rate_missing` and `tax_rate_invalid` — the invalid case never also emits `tax_rate_missing` — but both return `tax_rate_percent = null` and `tax_rate_effective_at = null`, both leave tax, margin, and margin percent unavailable, and **neither blocks physical production**. The raw invalid value is never returned as an authoritative rate and never reaches a readiness DTO, a confirmation request, or a `ProductionBatch` snapshot.
- **Timestamps.** Storage stays `YYYY-MM-DD HH:MM:SS` UTC SQLite text (no `T`, no `Z`, no offset) for `AppSetting.updated_at` and the future `tax_rate_effective_at_snapshot`; the API and confirmation context use `YYYY-MM-DDTHH:MM:SSZ`. Local time, arbitrary offsets, fractional seconds, a space instead of `T`, and a missing `Z` are rejected with `422 invalid_tax_rate_context`, and the API never exposes the raw stored form.
- **Warnings stay non-blocking.** The existing `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` codes and the exact existing `ProductionReadinessIssue` structure are preserved; only the two codes above are added; no aliases are introduced; and `can_produce` stays governed only by recipe/formula readiness, stock, lots, packaging, order lifecycle, and existing physical safety rules.
- **Readiness API mapping.** The existing endpoint is extended additively. `estimated_cost`, `estimated_tax`, and `estimated_margin` are **reused**; only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status` are added. `estimated_total_cost` is not authorized.
- **Snapshots.** `C2-II` adds exactly two nullable `ProductionBatch` columns, `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`, never backfilled, reusing the existing financial fields with no duplicate monetary snapshots, and reads the setting inside the production transaction through a bounded `connection`-aware extension of the C1 service.
- **Confirmation context.** `expected_tax_rate_percent` and `expected_tax_rate_effective_at` are required-but-nullable and declared without defaults. `null/null` means readiness observed **no valid configured tax rate** — a missing row **or** an invalid persisted value — not only an absent row. **Omission is not the same as explicit `null/null`** (`422 tax_rate_context_required`), and a partial-null, malformed, non-canonical, or out-of-range context is `422 invalid_tax_rate_context`. Stale conflict `409 tax_rate_context_stale`, writing nothing, fires on valid → changed valid, valid → missing, valid → invalid, missing → valid, and invalid → valid; **missing ↔ invalid is deliberately not a conflict**, because both produce the same financial result. An accepted no-valid-rate confirmation persists null rate snapshots and null tax, margin, and margin percent while completing physical production normally, and never repairs, clears, rewrites, or audits the invalid setting.
- **Reports** read persisted snapshots only, never recalculate history with the current rate, and show old rows as unavailable rather than `0.00`.
- **Frontend** performs no financial arithmetic, and `frontend/src/main.ts` stays at **at most 6399 lines** throughout C2.

## C2-I — merged and exact-head verified (2026-07-28)

`C2-I` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). PR #151, final reviewed head `6f72bffc9a0d17839e3a74c69366fe17df8a318b`, merge commit `7b3dde8278f59658bfa3a81c09e643ea10319551`, merged `2026-07-28T04:22:13Z`, exact-head readiness API smoke `PASS — 113 checks / 0 failures`, complete backend suite `737 passed / 0 failed / 0 skipped`. Both the final head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 without reinterpreting it:

- **One pure domain module**, `backend/app/domain/production_financials.py` — `TaxRateContext`, `ProductionFinancialInputs`, the immutable `ProductionFinancialEstimate`, `FinancialEstimateStatus`, and `FinancialWarningCode`. It opens no connection, reads no repository, imports neither FastAPI nor Pydantic, builds no `ProductionReadinessIssue`, and writes nothing.
- **Service integration** through `ProductionReadinessService._estimate_financials`, replacing the previous `_estimate_money`. As merged, the rate was read only through the existing no-argument C1 `TaxRateSettingsService.get_tax_rate()`, and the transaction-aware `connection=` extension was deliberately left to `C2-II`.
- **The five additive response fields** — `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status` — plus activation of the reused `estimated_tax` and `estimated_margin`. `estimated_total_cost` is absent and no field was renamed, removed, or duplicated.
- **The two new warning codes** only, carried by the existing `ProductionReadinessIssue` structure. All financial warnings stay non-blocking and `can_produce` is untouched.
- **Invalid-rate re-validation.** Because the C1 Settings repair surface may still return the stored text for an externally corrupted row, `is_configured` alone is not trusted: the returned percentage is re-parsed through the existing C1 `parse_tax_rate_percent`, and anything that fails — or a row with no effective timestamp — becomes the no-valid-rate context with `tax_rate_invalid`, never a raw value, never a fabricated `0.00`, and never an unhandled HTTP `500`.
- **Read-only.** No migration, no schema change, no persistence write, no `AuditLog`, no `ProductionBatch` change, no report change. `frontend/src/main.ts` is unchanged at exactly `6399` lines and no frontend production source was touched.

## C2-II — merged and exact-head verified (2026-07-28)

`C2-II` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`**.

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #152 — `C2-II — Persist transactional production financial snapshots` |
| State | `MERGED`, base `main` |
| Final reviewed head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Merge commit | `c3a3a7b8db06fe85290216113b784123ed9b6b30` |
| Merged at | `2026-07-28T09:00:50Z` |
| Exact smoke-tested head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Accepted backend result | complete backend suite `883 passed / 0 failed / 0 skipped`; all `737` original merged-baseline node IDs still collected, zero renames |
| Accepted frontend result | all 15 focused frontend suites green, `0 failed` |
| Production build | `npm run build` — `PASS` |
| Exact-head migration smoke | `PASS — 41 checks / 0 failures` |
| Exact-head API smoke | `PASS — 57 checks / 0 failures` |
| Exact-head browser smoke | `PASS — all Orders-route checks / 0 failures` |
| `frontend/src/main.ts` final line count | `6399` |
| Migration `0019` delivered | yes — `0019_production_batch_tax_rate_snapshots` |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |

`origin/main` equals the PR #152 merge commit, and both the final reviewed head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 without reinterpreting or expanding it:

- **One additive migration**, `0019_production_batch_tax_rate_snapshots`, adding only the two nullable `TEXT` columns `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `production_batches` — no default, no backfill, no table rebuild, no new table, and no duplicate monetary column. Existing rows keep every value and read `NULL` for both.
- **The bounded transaction-aware read.** `TaxRateSettingsService.get_tax_rate(connection=None)` — the no-argument behavior is unchanged, and a supplied connection reads `default_tax_rate` through the existing `SettingsRepository` on that exact connection, writing nothing and auditing nothing. No second tax-setting service, no raw `AppSetting` parsing in the confirmation service, and no generic transaction service locator.
- **One shared reducer**, `backend/app/services/tax_rate_context.py`, used by both readiness and confirmation. Missing and invalid both reduce to the comparable `null/null` context; the missing-versus-invalid distinction survives only where readiness warning generation needs it. `TaxRateContext` now rejects impossible state combinations outright.
- **The required-but-nullable request context**, validated in `backend/app/domain/production_tax_context.py` before anything is written. Omission is `422 tax_rate_context_required`; a partial-null, non-string, malformed, non-canonical, or out-of-range value is `422 invalid_tax_rate_context`. Both are returned in the repository's normal structured error contract, never as raw Pydantic internals.
- **The stale-context comparison**, run inside the existing `BEGIN IMMEDIATE` transaction before the first production write, raising `409 tax_rate_context_stale` with safe Russian guidance. Every row of the accepted matrix behaves exactly as decided, including the deliberate non-conflicts missing → invalid and invalid → missing.
- **Immutable financial snapshots** written in the same transaction as the batch, the ingredient and packaging snapshots and write-offs, the Order transition, and the `production_confirmed` audit. The arithmetic reuses the merged `C2-I` pure domain calculation; no formula is duplicated in `ProductionConfirmationService`.
- **One timestamp boundary**, `backend/app/domain/tax_rate_timestamps.py`, converting between the `YYYY-MM-DD HH:MM:SS` storage form and the `YYYY-MM-DDTHH:MM:SSZ` API form. The raw stored text never reaches a response.
- **A narrow API exposure boundary.** The two snapshots appear in the confirmation response and the `ProductionBatch` detail response only. The `ProductionBatch` list response, every report read model, every report API response, and the report UI are unchanged.
- **Minimal frontend integration.** `frontend/src/order-production-context.ts` owns the readiness context and request construction; the readiness DTO guard now requires the context pair and never fabricates `null/null`; a stale `409` is classified as a known no-write conflict that invalidates the cached readiness, closes the confirmation, and demands a fresh check without any automatic retry. No financial arithmetic and no financial presentation were added, and `frontend/src/main.ts` is unchanged at exactly `6399` lines.

## C2-III-A — merged and exact-head verified (2026-07-28)

`C2-III-A — Order and ProductionBatch financial presentation` is:

```text
C2-III-A — Order and ProductionBatch financial presentation:
DONE — MERGED AND EXACT-HEAD VERIFIED
```

`VERIFIED FROM MERGED PR #154 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #154 — `C2-III-A — Present Order and ProductionBatch financials` |
| State | `MERGED`, base `main` |
| Final reviewed head | `ef1103811a8f062f9129bfb465a98e0cfa388935` |
| Merge commit | `d432fcaee52a16a4f8b609ec160cf3fa2b33d013` |
| Merged at | `2026-07-28T13:05:34Z` |
| Exact smoke-tested head | `ef1103811a8f062f9129bfb465a98e0cfa388935` — identical to the final reviewed head |
| Focused frontend suites | `order-readiness-presentation` `19 pass`; `order-mutation-lifecycle` `33 pass`; `order-production-context` `25 pass`; `order-production-feedback` `21 pass`; new `production-financial-presentation` `22 pass` — all `0 fail / 0 skipped` |
| Complete frontend test-script result | all 16 `test:*` scripts pass, `0 failed`, `0 skipped` |
| Frontend production build | `npm run build` — `PASS` |
| Focused backend result | `test_production_readiness.py`, `test_production_batches_api.py`, `test_production_tax_snapshots.py`, `test_production_confirmation.py` → `160 passed / 0 failed / 0 skipped` |
| Complete backend result | `883 passed / 0 failed / 0 skipped` — byte-identical to the pre-change baseline, all `883` baseline node IDs still collected, zero renames |
| Exact-head API smoke | `PASS — 67 checks / 0 failures` |
| Exact-head browser smoke | `PASS — 28 checks / 0 failures` |
| `frontend/src/main.ts` | `6399` before → `6398` after |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |
| Backend formulas, persistence, migrations and reports | unchanged in `C2-III-A` |

`origin/main` equals the PR #154 merge commit, and both the final reviewed head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 and `docs/implementation-plan.md` § 11 without reinterpreting them:

- **Two focused frontend modules.** `frontend/src/production-financial-contract.ts` holds the financial DTO types, the three-value `financial_estimate_status` enum, and the readiness financial validation; `frontend/src/production-financial-presentation.ts` holds every financial render function. No catch-all `finance.ts`, `utils.ts`, `helpers.ts`, `manager.ts`, or `common.ts` was created, and the canonical tax-rate pair checks stay in the existing `order-production-context.ts`.
- **Order readiness financial presentation.** One financial block inside the existing readiness result card showing `Цена продажи`, `Ориентировочная себестоимость`, `Ставка налога`, `Налог`, `Маржа`, and `Маржа, %`, with `Ставка действует с: <formatted timestamp>` through the existing application date/time formatter when a rate is configured, and the backend status rendered as `Доступно` / `Частично` / `Недоступно` on an existing pill. The status is never inferred from which fields are null.
- **Immutable actual result.** One shared `Фактическая экономика партии` block renders the persisted `ProductionBatch` snapshot after successful production **and** when an existing batch of a produced or delivered Order is opened, so the two can never drift apart. No estimate-versus-actual variance is calculated or shown, and the current Settings rate is never compared with a historical snapshot.
- **Production history list.** A compact operational summary using only the five existing list fields — sale price, total cost, tax, margin, margin percent. The rate snapshots stay detail-only; no aggregate, total, sort, filter, or second list endpoint was added, and existing search, selection, loading, retained-snapshot and error behavior is unchanged.
- **DTO validation.** A trusted readiness result now requires every additive financial key, a `financial_estimate_status` that is exactly `available`, `partial`, or `unavailable`, and a rate context that is either a canonical pair or explicit `null/null`. `ProductionBatch` detail now requires **both** rate-snapshot keys present; a missing key is an outdated response rather than an implicit null. Malformed or partially populated context reaches the existing untrusted-response path, and nothing is normalized or repaired. The batch list contract is unchanged and still carries no rate snapshots.
- **Value semantics.** Backend `"0.00"` renders as a real zero; `null` renders as `Недоступно` and never as `0`, `0.00`, `0 ₽`, or `0%`; a negative margin and a negative margin percent keep their sign and are marked as negative.
- **No frontend arithmetic.** No money, percentage, or tax-rate value is converted to a JavaScript number, and no tax, margin, margin-percent, status, or variance is derived in the frontend.
- **Backend unchanged.** No formula, readiness status calculation, warning generation, tax-rate setting behavior, production confirmation, persistence, migration, snapshot, report query, report schema, or report document was changed; no endpoint was added; and no backend test was modified. The complete backend suite is unchanged at `883 passed / 0 failed / 0 skipped` with all `883` baseline node IDs still collected.
- **`frontend/src/main.ts` `6399` before → `6398` after.** The file did not grow; the two per-line batch cost-snapshot tables moved into the focused presentation module.
- **Physical readiness untouched.** `can_produce`, the physical readiness status, the stale-result ownership and the production guard behave exactly as before, and backend financial warnings are still shown once through the existing readiness warning section.

## C2-III-B — merged and exact-head verified (2026-07-28)

`C2-III-B — Snapshot-backed reports and report documents` is:

```text
C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED
```

`VERIFIED FROM MERGED PR #157 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #157 — `C2-III-B — Implement snapshot-backed reports and report documents` |
| State | `MERGED`, base `main` |
| Head branch | `codex/c2-iii-b-snapshot-backed-reports` |
| Final reviewed head | `305d5421e79b8cb833df9588e705e9418781e021` |
| Merge commit | `87410910aad472343c057f0bcbfcc3797f8b8e09` |
| Merged at | `2026-07-28T22:21:18Z` |
| Exact-head API smoke | `PASS — 53 checks / 0 failures` |
| Exact-head browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Complete backend suite | `942 passed / 0 failed / 0 skipped` |
| Focused report frontend suite | `54 pass / 0 fail` |
| All 17 frontend test scripts | `PASS` |
| Production build | `PASS` |
| `frontend/src/main.ts` | `6398` lines |

All of the above is **merged PR #157 evidence**. None of it was re-executed in this documentation-only pull request.

`origin/main` equals the PR #157 merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, and no commit exists on `main` after it.

Delivered on merged `main`: reports read persisted `ProductionBatch` financial snapshots only, through the pure aggregation in `backend/app/domain/report_financials.py`; the additive `FinanceReportResponse` fields `known_tax`, `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count`; the three additive warnings `tax_unavailable`, `partial_tax_basis`, `margin_percent_unavailable_zero_basis`; the `/reports` Overview and Finance presentation in `frontend/src/report-financial-contract.ts` and `frontend/src/report-financial-presentation.ts`; and the snapshot-backed finance section of a newly generated «Сводка мастерской». Previously generated documents remain byte-identical.

**Reports on merged `main` are snapshot-backed.** The former paired-input margin derivation is gone from `main`.

## C2 — COMPLETED

```text
C2 — COMPLETED
C2-III-B — DONE — MERGED AND EXACT-HEAD VERIFIED
```

Every C2 slice is merged, exact-head verified and closed: `C2-I` (PR #151), `C2-II` (PR #152), `C2-III-A` (PR #154) and `C2-III-B` (PR #157). The `C2-III` planning umbrella was subdivided into exactly `C2-III-A` and `C2-III-B`, and both are done. C2 is **not reopened**.

C2 being complete does **not** make the product release-ready. Restore, packaging, installation verification, the update flow and the full release-candidate smoke all remain open, and **product release readiness is not claimed**.

## HISTORICAL — SUPERSEDED — C3-II-A implemented on its PR branch (2026-07-30)

> This section was true before PR #161 merged and before CR-009 was accepted.
> The active lifecycle is at the top of this file.

```text
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — IMPLEMENTED ON PR BRANCH — NOT MERGED
C3-II-B — NEEDS PRODUCT DECISION — NOT AUTHORIZED
C3 — INCOMPLETE
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

PR #159 merged on `2026-07-30T03:20:23Z` from final reviewed and published head `bf7cde060a43190fdf22c612a16b0c137aa5531b` at merge commit `ba3ca7443e3280bc7f700af11e75dc4fa810665f`. `GET /api/audit-logs` and `/settings/audit-log` are on merged `main`.

Exact-final-head evidence is limited to frontend and browser evidence: focused AuditLog suite `92 passed / 0 failed / 0 skipped` in the default and `TZ=Europe/Amsterdam` runs; every frontend `test:*` script `PASS — 0 failed / 0 skipped`; build `PASS`; `frontend/src/main.ts` `6380`; browser smoke `PASS — EXACT-HEAD BROWSER SMOKE PASSED`, 60 scenarios. Backend `1364 passed / 0 failed`, focused backend `422 passed`, 942 preserved node IDs and API smoke `150 checks / 0 failures` were executed on `2848880f2009158749398aec7d504c0364336ba9`. The backend tree is byte-identical at `bf7cde060a43190fdf22c612a16b0c137aa5531b`, but those runs were not re-executed there and are not relabelled as exact-final-head evidence.

`C3-II-A` now implements only atomic workshop-profile audit on the PR branch: a real canonical profile upsert and exactly one safe `workshop_profile.updated` event share one caller-owned SQLite transaction; failure of either write commits neither; canonical no-op preserves `updated_at` and writes neither; summaries and bounded metadata contain no profile values. Existing API shape, Settings lifecycle and historical documents remain unchanged. Durable contract: `docs/audit-log.md` § 16, `docs/settings.md`, `docs/api.md`, `docs/implementation-plan.md`.

`C3-II-B` covers only manual backup, JSON export and report-document auditing. It is unresolved because a successfully created filesystem artifact followed by a failed SQLite AuditLog insert has no accepted truthful result, compensation, retry or recovery policy. It is not authorized. `CR-004` and `CR-006` remain unchanged and separate.

## HISTORICAL — SUPERSEDED — C3-I implemented on its PR branch, not merged (2026-07-29)

> This section records the true pre-merge state of PR #159. It is superseded by the current lifecycle section above and must not be read as a current repository claim.

```text
C3-I — Read-only AuditLog workspace
IMPLEMENTED ON PR BRANCH — NOT MERGED
```

Branch `codex/c3-i-read-only-audit-log-workspace`, started from clean `origin/main` `fa433d03acbf68e16b14ba6245885ab9eaf15c35` (the PR #158 merge commit, final reviewed head `4a37f6700e147fb83b64be29db4793e3579a7eff`). This is **not** `DONE`, `COMPLETED` or `MERGED`: it awaits review and merge, and product release readiness is **not** claimed.

The durable contract is `docs/audit-log.md` and was not reinterpreted. The single implementation-level clarification `C3-I` adds is the exact nested `filter_options` DTO and the omission of `null` from selectable entity types, recorded in `docs/audit-log.md` § 7.5.1 and `docs/api.md`.

### Delivered

- **Backend.** `GET /api/audit-logs` only — no detail endpoint, no write surface. Route `backend/app/api/audit_logs.py` → service `backend/app/services/audit_logs.py` → repository reads in `backend/app/repositories/audit.py`, with the pure `backend/app/domain/audit_log_presentation.py` (50 action labels, 19 entity labels, 2 actor labels, the three unknown-code fallbacks, the 50-row generic summary table and the exact 21-action suffix allowlist) and the pure `backend/app/domain/audit_log_query.py` (ordered pagination precedence and date validation). Schemas in `backend/app/schemas/audit_logs.py` use `extra="forbid"` so a forbidden field cannot be serialized accidentally.
- **Privacy.** The raw persisted `summary`, `metadata_json`, `entity_id`, `source` and `source_label` are absent from every response. Wish titles, individual-recipe titles and internal IDs never appear anywhere in the serialized JSON. `client_wish.*`, `client_recipe.*`, every ID-bearing action and every catalog-assignment action are excluded from the allowlist, which is an exact 21-row table rather than a prefix glob.
- **Validation.** `PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"` is the only new `DomainIssueCode` member. `limit=-1` is `negative_quantity` only; `limit=0` and `limit=201` are `pagination_out_of_range` only. The date-range conflict returns `field: created_before`. Every rejection uses the `{"detail": {...}}` envelope, never raw Pydantic internals — the route accepts raw query text precisely so typed parsing cannot replace the contract.
- **Read-only.** Reads write no AuditLog row, mutate no business table, create no file and change no setting; historical rows are byte-identical before and after. `AuditLogRepository.create_log` has an empty diff and no production write call site changed.
- **Frontend.** Route `/settings/audit-log`, navigation entry `Журнал действий` under `Данные и настройки`, with date/action/entity/actor filters combining with AND, `Очистить фильтры`, `Обновить`, `Показать ещё`, and the loading, empty, filtered-empty, initial-failure-with-retry, refresh-failure-retaining-rows, load-more-failure-retaining-rows, all-loaded, structured-422, narrow-viewport and keyboard states. Focused modules `audit-log-contract.ts`, `audit-log-presentation.ts`, `audit-log-workspace.ts`, `audit-log-bindings.ts` and the extracted `app-navigation-routes.ts` — no `utils`/`helpers`/`manager`/`common` dumping ground.
- **No migration**, no column, table, index, trigger, backfill or data rewrite. No dependency and no lockfile change.

### Accepted results

| Check | Result |
|---|---|
| Complete backend suite | `1364 passed / 0 failed / 0 skipped` |
| Merged baseline node IDs still collected | all `942`, zero renames |
| Focused `C3-I` backend tests | `422 passed` |
| Focused frontend suite `test:audit-log-workspace` | `82 passed / 0 failed / 0 skipped` |
| `TZ=Europe/Amsterdam` focused frontend suite | `82 passed / 0 failed / 0 skipped` |
| Frontend `test:*` scripts | `18` (was `17`) — all pass |
| Frontend production build | `PASS` |
| `git diff --check` | clean |
| `frontend/src/main.ts` | `6398` before → `6380` after |

Exact-head API and browser smoke results are recorded in the pull request body against the exact published head.

### Known gaps and limitations

- The `docs/audit-log.md` § 11.6 coverage gap stands: backup, export, report-document and workshop-profile actions are still not audited, so the journal does not show them. `C3-I` is read-only and must not add those write call sites.
- A true process `source` remains deferred; only `actor_type` exists.
- No detail endpoint, no metadata viewer, no raw JSON viewer, no export, no search, no analytics.
- C2 stays closed; C4 stays `INACTIVE — NEEDS PRODUCT DECISION`; **product release readiness is not claimed**.

## HISTORICAL — SUPERSEDED — the then-authorized C3 slice, C3-I

```text
C3-I — Read-only AuditLog workspace
IMPLEMENTED ON PR BRANCH — NOT MERGED
```

`C3-I` is the **only** authorized C3 runtime slice. It is implemented on `codex/c3-i-read-only-audit-log-workspace` and awaits review and merge. The accepted boundary below is unchanged and is what the implementation was held to.

The durable product, API, privacy and presentation contract is **`docs/audit-log.md`**. It is authoritative; the summary below does not replace it.

- **Purpose.** A plain-language history of important workshop actions — `Журнал действий` — so the user can understand what happened without opening SQLite, JSON, logs, GitHub or a terminal. Not a technical admin console, database browser, SIEM, analytics, rollback, event editor or debugging console.
- **Actor field — `actor_type`, not `source`.** The API keeps the persisted column name: `actor_type` and `actor_label`. **No `source` field is exposed or authorized.** The values that exist, `system` and `user`, describe the **actor that initiated the action**, not a process origin, so mapping them onto `source` would silently change the field's meaning. Labels: `system → Система`, `user → Пользователь`, anything else → `Другой инициатор`. The historical process vocabulary (`manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore`) is **aspirational** — no write call site persists that dimension — so a true `source` is **deferred** to a separately authorized decision and write-side slice. No column rename, no migration, no backfill, no write-call-site change.
- **API.** Exactly one new endpoint, `GET /api/audit-logs`. The old roadmap proposal `GET /api/audit-logs/{id}` is **explicitly superseded for the MVP**. No create, update, delete, rollback or export endpoint.
- **Safe read model.** The response carries `items`, `total`, `limit`, `offset`, `filter_options`; each item carries exactly `id`, `created_at`, `action`, `action_label`, `entity_type`, `entity_label`, `display_summary`, `actor_type`, `actor_label`. The raw persisted summary and raw `metadata_json` are never returned, and neither are `entity_id`, table names, stack traces, SQL, filesystem paths or raw payloads.
- **`display_summary`.** The raw `audit_logs.summary` is **never returned verbatim and is never used as an unrestricted API or frontend fallback** — it is write-time technical text, mostly English, sometimes carrying internal record IDs, and `client_wish.*` values carry user-authored wish text. A focused backend presenter (`AuditLogDisplayPresenter` or an equivalently focused module) resolves a safe Russian `display_summary` from the known `action`: no internal IDs, no metadata, no business-table join, no historical rewrite, no sensitive text.
- **Bounded suffix extraction.** A suffix from the persisted summary may contribute to `display_summary` only when **all seven** conditions hold: the action is explicitly allowlisted; the summary starts with the exact prefix assigned to that action; the suffix is non-empty; the action may retain that category of business name; the suffix is plain text only; the suffix carries no presenter-supplied internal identifier; and no database or metadata lookup happens. Otherwise the generic action-specific phrase applies. The allowlist is the exact 21-row table in `docs/audit-log.md` § 6.4.3 — not a prefix glob — and excludes `client_wish.*`, `client_recipe.*`, every ID-bearing action and every catalog-assignment action. Returning the complete summary, its English prefix, or using it as an unrestricted fallback stays prohibited.
- **Ordering and pagination.** `created_at DESC, id DESC`; `limit` default `50`, accepted integer range `1..200`; `offset` default `0`, accepted integer range `0..9223372036854775807`. Validation runs in a fixed order and the first match decides the code: missing → default; wrong type, fractional or boolean → `non_integer_quantity`; negative integer → `negative_quantity`; non-negative `limit` outside `1..200` or `offset` above the SQLite maximum → `pagination_out_of_range`. Bounds are compared on raw decimal text before conversion, so arbitrary-length values cannot become a Python conversion failure or oversized SQLite bind. Invalid values are **rejected, never silently clamped**. No unbounded history.
- **Filters.** `created_from` (inclusive), `created_before` (exclusive), `action`, `entity_type`, `actor_type`, `limit`, `offset` — **no `source` filter** — combined with logical AND, with ISO-8601 UTC timestamps, structured `422` with the existing `invalid_date` code for malformed input, filter options derived from values that actually exist as rows in `audit_logs`, and no writes.
- **Validation wire shape.** The routers raise `HTTPException(status_code=422, detail=issue.__dict__)`, so the `DomainIssue` is the **value of `detail`**, and the body is `{"detail": {"code", "message", "field", "value", "next_action"}}`. Codes: `invalid_date`, `non_integer_quantity`, `negative_quantity`, and one new authorized enum member `PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"`, which must not be replaced by `percentage_out_of_range`, `invalid_category`, `invalid_decimal` or `zero_quantity`.
- **Date-range conflict.** `created_before <= created_from` returns HTTP `422`, `code: invalid_date`, **`field: created_before`**, `value` the supplied `created_before`, a Russian `message` saying the end of the period must be later than its beginning, and a Russian `next_action` telling the user to pick a later end date. No synthetic `date_range` field.
- **Read-only.** Reads write no AuditLog record, mutate no business table, create no file, change no setting, trigger no regeneration, and perform no cleanup or normalization of historical rows. AuditLog remains append-only — the presenter changes only what is shown.
- **Frontend.** Canonical route `/settings/audit-log`, title `Журнал действий`, with the full state set — loading, empty, filtered-empty, refresh failure retaining the previously accepted list, initial-load failure, narrow viewport and keyboard accessibility. Filters are date, action, entity and actor. No raw codes, no raw persisted summary, no JSON, no `metadata_json`, no table names, no internal entity IDs, no stack traces, no SQL, no developer paths and no GitHub or PR terminology. Focused modules only; `frontend/src/main.ts` must not grow net.

### C3-I non-goals

AuditLog edit; AuditLog delete; rollback or undo; restore from AuditLog; detail endpoint; metadata viewer; raw JSON viewer; returning the raw persisted summary through any field or fallback; a `source` field, a `source_label` field or a source filter; persisting a new source/process dimension; CSV/XLSX/PDF audit export; charts; analytics; search over sensitive text; roles or permissions; multi-user actors; remote audit shipping; cloud sync; retention policies; log compaction; schema migration; backfill; changes to existing write semantics; C4; Restore; packaging; update flow; release-candidate smoke.

### Historical `C2-III-B` authorization boundary

> **HISTORICAL — the authorization text as written before PR #157 merged.** It is preserved because it is the boundary the merged slice was held to. `C2-III-B` is now `DONE — MERGED AND EXACT-HEAD VERIFIED`; the paragraphs below must not be read as describing open work.

One bounded backend-plus-frontend report vertical:

```text
persisted ProductionBatch financial snapshots
→ backend report aggregation
→ report DTOs
→ /reports presentation
→ overview report consumers
→ generated «Сводка мастерской»
```

**Backend report ownership.** The affected financial reports must read persisted `ProductionBatch` financial snapshots. Report tax comes only from persisted `ProductionBatch.tax`; report margin comes only from persisted `ProductionBatch.margin`; historical rate changes never modify existing report results; the current Settings tax rate is never applied retroactively; report calculations remain backend-owned; report endpoints remain read-only; and report reads create no audit records and no business mutations.

**Missing, zero and negative values.** An explicit stored `"0.00"` stays a real known zero; `null` stays unavailable or incomplete; a negative margin and a negative margin percentage stay valid signed information; and a missing historical snapshot stays different from configured zero tax. A null snapshot must never be included as a fabricated `0`, `0.00`, `0 ₽`, or `0%`. Old batches with incomplete financial snapshots must contribute to explicit incomplete-data counters or warnings rather than silently appearing complete.

**Aggregate basis — conflict found and resolved.** This paragraph previously said no new aggregate margin-percent formula was defined and required the runtime task to **stop and report the exact conflict** if the documented paired basis contradicted snapshot-backed aggregation. That happened. The read-only Phase 0 audit stopped with `C2-III-B — BLOCKED BY REPORT AGGREGATION CONTRACT CONFLICT` and created no branch, edit, commit or PR: the paired sale-price/cost set `P` and the persisted-margin set `M` are the same set only while margin is derived, and diverge as soon as reports read snapshots, because pre-`C2-II` rows carry a known sale price and total cost with `tax` and `margin` both `null`.

The accepted resolution is now recorded in `docs/reports.md` § *Accepted `C2-III-B` snapshot aggregation contract* and in ADR 0012 § *Accepted clarification — snapshot report aggregation contract*: `known_margin` is the sum of persisted `ProductionBatch.margin` over `M`; `known_margin_percent` is `ROUND_PERCENT(Σ margin over M ÷ Σ sale_price over M × 100)`, `null` when `M` is empty or that denominator is zero; `known_tax` is the sum of persisted `ProductionBatch.tax`. The global `known_revenue` is never the denominator, and persisted row `margin_percent` is never summed or averaged. `complete_finance_record_count` and `incomplete_margin_count` keep their paired sale-price/cost meanings and are not snapshot-coverage counters; the additive fields are `known_tax`, `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count`; the additive warnings are `tax_unavailable`, `partial_tax_basis`, `margin_percent_unavailable_zero_basis`.

**Report DTO and UI boundary.** Synchronized changes are authorized in the affected finance report backend model, the affected overview finance summary, the corresponding API schemas, frontend `/reports`, backend-provided report warnings, and document generation for `Сводка мастерской` where it consumes the affected report DTO. The frontend displays backend report DTOs and backend warnings; it must not calculate report tax, report margin, report margin percentage, incomplete-data coverage, or historical financial values.

**Report documents.** `Сводка мастерской` stays synchronized with the report DTO it consumes. Newly generated documents may reflect the snapshot-backed report result. Previously generated documents remain immutable and are never rewritten, regenerated, or silently replaced. Document generation remains an explicit user action.

**Explicit exclusions.** `C2-III-B` must not change Orders readiness; Order production confirmation; the Order lifecycle; `ProductionBatch` persistence; `ProductionBatch` list presentation; `ProductionBatch` detail presentation; the `C2-III-A` financial presentation modules; tax-rate Settings behavior; migrations; historical `ProductionBatch` rows; or stock and production transactions.

### C2 completion boundary — satisfied

> **HISTORICAL — SATISFIED.** This boundary read: *"C2 remains incomplete until `C2-III-B` is reviewed, exact-head verified and merged, and its active lifecycle is closed."* All three conditions are met — PR #157 was reviewed, exact-head verified and merged at `87410910aad472343c057f0bcbfcc3797f8b8e09`, and this document closes its active lifecycle. **C2 is COMPLETED.** C4 remains inactive, and product release readiness is not claimed.

## R4 merge closure

`R4` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`
- Merged at: `2026-07-27T08:51:06Z`

Both original filename nodes are closed on `main`:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

## CR-005 status

`CR-005` remains **accepted** and **implemented**. The durable contract is unchanged and lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. The canonical filename reason segment is owned by the shared backend helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the export JSON manifest continues to carry the normalized human reason.

`R4` is closed and is **not reopened**. `CR-005` is closed and is **not reopened**.

## CR-006 — export create-response confirmation semantics — ACCEPTED (2026-08-01)

```text
CR-006 — ACCEPTED — PRODUCT DEFECT CONFIRMED AND CONTRACT DECIDED
```

The evidence-only diagnostic is **complete**. It was executed against
`origin/main` = `1d4e90ccffb6f154882e685b09803f67f2f75ceb` through the real
FastAPI route and the real `create_json_export`, with an isolated migrated
SQLite database and an isolated export directory per scenario, and with faults
injected only at named OS boundaries (`pathlib.Path.stat`,
`pathlib.Path.iterdir`) and named module seams. **No production file was
changed**, and the temporary harness lived outside the repository and was not
committed.

**Reachability — answered.** The fallback is reachable in
production-equivalent behavior, not only through mocks. A per-file `stat`
failure on the exact created file during the endpoint's secondary
`list_export_files(...)` reaches it, and so does a directory-entry race between
`iterdir()` and that `stat`, in both cases while the created export is present
and correct on disk. When it runs, the response `reason` is the human manifest
reason `before-update ../unsafe` instead of the canonical
`before_update_unsafe`, which the frontend would render verbatim on `/exports`.
The same redundant re-scan can also return HTTP `500` after a fully successful
creation, and can match a foreign object that replaced the exact path and
report its size as the created export's size.

**Classification.**

```text
PRODUCT DEFECT — CREATE-RESPONSE CONTRACT MISMATCH
Severity: MEDIUM
```

No application-caused data loss, no overwrite, no incorrect export bytes, no
source database mutation, and no privacy exposure were found. A file removed by
an injected external actor after the creator returned is not application data
loss.

**Accepted contract.** A successfully returned `ExportResult` is the
authoritative result of the create operation; the create response is built only
from it; the API `reason` is parsed from the exact final filename through the
same canonical parsing contract list and status use; `ExportResult.reason` is
never the API reason; `list_export_files` leaves the create path but stays
authoritative for the independent `GET` reads, whose contract is unchanged;
`201 Created` describes the operation boundary and promises no permanent
retention; a creator that does not return successfully is never reported as
success.

**Preserved boundaries.** `CR-005`, `R4`, `CR-009` and `C3-II-B1` are **not
reopened**; the export manifest keeps the normalized human reason; the export
schema version is unchanged; no sidecar, metadata table, second persisted
reason or new API reason field; no migration; no production change in the
decision itself.

**Adjacent findings, separated and not resolved by `CR-006`:** the creator's own
post-write `stat` at `backend/app/services/export.py:266` escaping as a raw
`OSError` while a complete export remains on disk, and the `GET` list/status
behavior under the same read failures.

`CR-006` is not part of `CR-004`, is not a reason to reopen `CR-005`, and is not
a reason to reopen `R4`. It is **not** a fifth backend baseline failure. Durable
decision: `docs/decisions/0014-json-export-create-confirmation-semantics.md`.
Completed evidence: `docs/backend-baseline-failure-triage.md` §17.5.

## Remaining release obligations

None of these is activated here.

- `CR-004` is **accepted and implemented**; no change request remains in `needs evidence`.
- The Restore **product decision is complete** — `CR-010`, ADR 0016, launcher-assisted. Restore **implementation** remains open and Restore is **not implemented**.
- Final macOS packaging and user-ready launch remains **open** and **not completed**.
- Installation verification remains **open**.
- Packaged update flow and update smoke remain **open** and **not completed**.
- Full release-candidate smoke remains **open** and **not completed**.
- C1 and C2 are **complete**. C3 is `COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED`: C3-I, C3-II-A, C3-II-B1, C3-II-B2 and C3-II-B3 are all merged, and the artifact-finalization hardening merged as PR #168. `CR-004`, `CR-006` and `CR-009` are accepted and implemented. C4 has an accepted product decision and **no implementation**; `C4-I` is the only authorized future runtime slice, and it is authorized only after this documentation PR merges.
- Continuing documentation accuracy remains an ongoing obligation.

**Product release readiness is not claimed.**
