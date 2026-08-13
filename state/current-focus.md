# Current focus

Updated: `2026-08-13`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED
D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Next allowed task

**D4-A — Version identity and compatibility preflight only.**

Implement one application-version truth and ordinary-startup read-only schema-lineage preflight. Fail closed on newer/unsupported existing lineage before backup, migrations, backend start or browser handoff.

D4-A must reuse/generalize the existing migration-lineage classifier and must not reopen Restore.

## Do not start

- D4-B staged migration/UpdateLog;
- D4-C UI/failure UX;
- D4-D exact-package closure;
- D5;
- auto-update/download;
- signing/notarization/DMG/App Store;
- release readiness;
- Restore changes.

Normative decision: `docs/decisions/0020-d4-update-safety-contract.md`.
