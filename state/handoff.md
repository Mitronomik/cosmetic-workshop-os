# Handoff

Updated: `2026-08-13`

## Current authority

- Restore is closed and must not be reopened by D4.
- D3 package MVP is implemented.
- CR-013 / ADR 0020 decides D4 Update Safety.
- Only D4-A is authorized next.

The exact pre-CR-013 handoff is preserved in `docs/history/d4-pre-decision/handoff.md`.

## Closed lifecycle truth

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

## Lifecycle

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED
D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## D4-A handoff

Implement only:

1. one canonical repository-owned product version;
2. generated package/runtime projections of that version;
3. backend read-only effective version status;
4. ordinary-startup read-only migration-lineage preflight;
5. fail-closed newer/unsupported/unreadable existing lineage before mutation;
6. first-run only when canonical DB file is absent;
7. focused backend/launcher/package tests.

Do not implement staged migration, UpdateLog, frontend update status, packaged update-failure UX or any D4-B/C/D behavior in D4-A.

If reuse requires changing a protected Restore production blob, stop and open a separate decision.
