# Current focus

Updated: `2026-08-13`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Verify the D4-B implementation only; do not start D4-C.**

D4-A remains the closed pre-mutation authority. The current D4-B changeset adds only the supported-older update execution seam:

- verified `before_migration` backup;
- runner-owned consistent stage;
- staged migration + exact target verification;
- canonical stability/sidecar guards and atomic commit;
- durable external UpdateLog;
- conservative interrupted-operation reconciliation;
- ownership-proven cleanup of stage and stage sidecars.

D4-B is implemented but not merged/verified/lifecycle-closed. D4-C remains unauthorized.

## Do not start

- D4-C UI/failure UX;
- D4-D exact-package closure;
- D5;
- auto-update/download;
- signing/notarization/DMG/App Store;
- release readiness;
- Restore changes.

Normative decision: `docs/decisions/0020-d4-update-safety-contract.md`.
