# Handoff

Updated: `2026-08-13`

## Current authority

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 decides D4 Update Safety.
- D4-A is DONE — merged and exact-head verified.
- D4-B is DONE — merged, exact-head/exact-package verified and lifecycle-closed.
- D4-C is DONE — merged, exact-head/exact-package verified and lifecycle-closed.
- D4-D is AUTHORIZED NEXT — not implemented.

The exact pre-CR-013 handoff is preserved in `docs/history/d4-pre-decision/handoff.md`.

## Lifecycle

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## D4-C closed handoff / D4-D next

Load-bearing implementation seams:

1. `backend/VERSION` — only editable product-version authority.
2. `backend/app/version.py` — validates and resolves repository vs packaged effective version without version ordering.
3. `scripts/package_macos.sh` — generates package version projections from the authority.
4. `scripts/verify_product_version.py` — build-time projection consistency gate.
5. `backend/app/db/startup_compatibility.py` — opens existing canonical DB read-only and delegates lineage classification to `app.db.migration_lineage`.
6. `backend/app/services/startup.py` — runs version + schema preflight before directory creation, backup or migrations.
7. `backend/app/services/runtime_identity.py` + thin Settings route — expose the same effective version read-only.

Supported older schemas now enter `backend/app/services/update_safety.py` after the closed D4-A gate. That service owns verified backup, consistent stage creation, stage-only migration, target verification, atomic canonical publication and external UpdateLog reconciliation; current/fresh/development paths retain their bounded existing behavior.

D4-C is closed on verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` with Level-5 runs `31747841343` / `31749503618` and a `0`-file head→merge compare. D4-D may now perform only final exact-package D4 verification and lifecycle closure; do not widen into D5, release work or Restore.

D4-A evidence remains recorded above. D4-B evidence: verified PR head `8688fa3dba87205b4b4626ebab2902262fd4cd24`, run `31716610699`, artifact `9187785415`; merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4`, run `31717705331`, artifact `9188228739`; compare `0` changed files.
