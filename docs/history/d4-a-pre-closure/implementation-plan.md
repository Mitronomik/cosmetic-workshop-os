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
D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

Normative D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.

## D4 programme

### D4-A — Version identity and compatibility preflight

**IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING**.

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

- supported older schemas still enter the existing `before_migration` backup and direct migration path after preflight;
- no UpdateLog exists yet;
- no frontend update presentation or new Finder error category exists;
- no protected Restore production file changes.

D4-A does **not** authorize D4-B by implementation alone. It must be merged, exact-head verified and lifecycle-closed first.

### D4-B — Safe migration execution and durable UpdateLog

**PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED**.

Planned architecture from ADR 0020:

```text
consistent before_migration backup
→ consistent runner-owned migration stage
→ migrate only stage
→ verify target lineage
→ atomic canonical publication
→ durable external UpdateLog
```

### D4-C — User-facing update status and packaged failure UX

**PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED**.

### D4-D — Exact-package update verification and lifecycle closure

**PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED**.

## D5 and release boundary

`D5 — Remote install checklist` remains **NOT AUTHORIZED BY CR-013**. Product release readiness remains **NOT CLAIMED**. Signing, notarization, DMG, App Store, release channels and auto-download remain out of scope.
