# Handoff

Updated: `2026-08-13`

## Current authority

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 decides D4 Update Safety.
- CR-014 / ADR 0021 decides D5 Remote Install Rehearsal and authorizes D5 only.
- D4-A is DONE — merged and exact-head verified.
- D4-B is DONE — merged, exact-head/exact-package verified and lifecycle-closed.
- D4-C is DONE — merged, exact-head/exact-package verified and lifecycle-closed.
- D4-D is DONE — final exact-package verification passed; D4 is lifecycle-closed.

The exact pre-CR-013 handoff is preserved in `docs/history/d4-pre-decision/handoff.md`.

## Lifecycle

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED
```

## D4 final closed handoff

Load-bearing implementation seams:

1. `backend/VERSION` — only editable product-version authority.
2. `backend/app/version.py` — validates and resolves repository vs packaged effective version without version ordering.
3. `scripts/package_macos.sh` — generates package version projections from the authority.
4. `scripts/verify_product_version.py` — build-time projection consistency gate.
5. `backend/app/db/startup_compatibility.py` — opens existing canonical DB read-only and delegates lineage classification to `app.db.migration_lineage`.
6. `backend/app/services/startup.py` — runs version + schema preflight before directory creation, backup or migrations.
7. `backend/app/services/runtime_identity.py` + thin Settings route — expose the same effective version read-only.

Supported older schemas now enter `backend/app/services/update_safety.py` after the closed D4-A gate. That service owns verified backup, consistent stage creation, stage-only migration, target verification, atomic canonical publication and external UpdateLog reconciliation; current/fresh/development paths retain their bounded existing behavior.

D4-C remains closed. D4-D final verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881` and D4 is lifecycle-closed. CR-014 now authorizes D5 only as documentation + assisted-install rehearsal; release/Phase 12/runtime/Restore expansion remains unauthorized.

D4-A evidence remains recorded above. D4-B evidence: verified PR head `8688fa3dba87205b4b4626ebab2902262fd4cd24`, run `31716610699`, artifact `9187785415`; merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4`, run `31717705331`, artifact `9188228739`; compare `0` changed files.

## CR-015 handoff

Next implementation work is only the native macOS application lifecycle blocker fix from ADR 0022. Preserve the existing browser UI, Python packaged entrypoint, launcher/backend ownership, external user-data boundary, Restore and D4 update semantics. Required acceptance proof includes a real packaged `.app` launched through LaunchServices, responsive application-level Quit (not direct SIGTERM as the sole proof), released ports/processes, repeat Finder launch and persistence, followed by a fresh human clean-Mac D5 rehearsal.
