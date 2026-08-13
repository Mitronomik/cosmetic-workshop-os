# Current focus

Updated: `2026-08-13`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Verify and lifecycle-close D4-A only.**

D4-A implementation now provides:

- one version authority (`backend/VERSION`) and generated package/runtime projections;
- backend read-only Settings/status version identity;
- ordinary-startup read-only migration-lineage preflight before backup/migration;
- fail-closed newer/unsupported/unreadable existing lineage;
- first-run only for a genuinely absent canonical DB path;
- focused backend/package tests.

Before D4-B can be authorized, D4-A must merge, pass exact-head verification and receive a separate lifecycle closure.

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
