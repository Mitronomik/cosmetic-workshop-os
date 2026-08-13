# Implementation plan

Status: **CURRENT**
Updated: `2026-08-13`

The exact pre-CR-013 plan is preserved in `docs/history/d4-pre-decision/implementation-plan.md` from base `dc2301f7d4e101ad0fba851325dae9274f02da0c`.

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

Normative D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.

## D4 programme

### D4-A — Version identity and compatibility preflight

**DONE — MERGED AND EXACT-HEAD VERIFIED**.

Implemented scope:

- one canonical repository version source at `backend/VERSION`;
- dynamic backend package metadata plus generated macOS package projections;
- package-version projection verifier;
- source/package effective runtime version resolver;
- backend Settings/status projection of that same effective value;
- read-only ordinary-startup compatibility wrapper reusing `app.db.migration_lineage`;
- fail-closed existing newer/unsupported/unreadable lineage before backup/migration;
- first-run classification only when the canonical DB path is genuinely absent;
- focused D4-A backend and package tests.

Intentionally unchanged:

- D4-A originally left supported-older migration execution unchanged; the closed D4-B slice now owns staged execution after preflight;
- D4-A itself introduced no UpdateLog; D4-B now owns the durable external UpdateLog;
- no frontend update presentation or new Finder error category exists;
- no protected Restore production file changes.

D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice.

### D4-B — Safe migration execution and durable UpdateLog

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Implemented D4-B architecture from ADR 0020:

```text
verified consistent before_migration backup
→ consistent runner-owned migration stage
→ migrate only stage
→ verify source/target lineage and canonical stability
→ atomic canonical publication
→ post-commit canonical verification
→ durable external UpdateLog
```

Implemented scope:

- external atomic `update-journal.json` with `started/completed/failed`;
- conservative reconciliation of interrupted `started` records;
- verified automatic backup as a hard staging prerequisite;
- stage created through the accepted SQLite Online Backup primitive, never raw file copy;
- migrations execute only against the stage;
- exact target lineage + SQLite structural verification before commit;
- same-directory atomic `os.replace` commit after canonical-change/sidecar guards;
- post-commit failures remain distinct from pre-commit migration failure;
- deterministic stage ownership validation before interrupted-artifact cleanup;
- no D4-C frontend or packaged failure-UX work.

D4-B closure remains satisfied. D4-C is also merged, verified and lifecycle-closed.

### D4-C — User-facing update status and packaged failure UX

**DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**.

Verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` are content-identical. Level-5 runs `31747841343` and `31749503618` passed the full regression, lifecycle, frontend, real package and exact-package D4-C smoke.

### D4-D — Exact-package update verification and lifecycle closure

**AUTHORIZED NEXT — NOT IMPLEMENTED**.

D4-D is limited to final exact-package verification of the complete ADR 0020 D4 manual-update safety contract and D4 lifecycle closure. It must not introduce new update runtime authority, downloader/checking, D5, release/distribution work or Restore changes.

## D5 and release boundary

`D5 — Remote install checklist` remains **NOT AUTHORIZED BY CR-013**. Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG, App Store, release channels and auto-download remain out of scope.
