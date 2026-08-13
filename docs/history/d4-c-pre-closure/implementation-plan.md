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
D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
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

D4-A and D4-B remain closed. D4-C is implemented in the current branch and awaits exact-head/exact-package verification and lifecycle closure.

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

D4-B closure remains satisfied. D4-C is implemented separately and remains verification-pending.

### D4-C — User-facing update status and packaged failure UX

**IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING**.

Implementation code commit: `adfe37a3f68a545635f173c22d4710eacde86e74`.

Implemented scope: redacted backend-owned Settings update status; compact read-only Settings presentation; two fixed packaged update-failure outcomes; no update controls or raw metadata; no protected Restore changes; focused backend/package/frontend tests.

D4-D remains unauthorized until D4-C is merged, verified and lifecycle-closed.

### D4-D — Exact-package update verification and lifecycle closure

**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.

## D5 and release boundary

`D5 — Remote install checklist` remains **NOT AUTHORIZED BY CR-013**. Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG, App Store, release channels and auto-download remain out of scope.
