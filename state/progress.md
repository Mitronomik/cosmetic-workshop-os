# Progress

Updated: `2026-08-13`

## Closed baseline

- C4-III exact-head and exact-package verification passed and the Restore lifecycle is closed.
- Restore is `IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`.
- D3 macOS package MVP is implemented.
- Product release readiness is not claimed.

The exact pre-CR-013 progress file is preserved in `docs/history/d4-pre-decision/progress.md`.

## Closed lifecycle truth

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

## CR-013 decision

`CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT`.

ADR 0020 decides:

- one repository-owned application-version truth with generated projections;
- ordered migration lineage remains schema authority;
- ordinary startup gains a read-only pre-mutation compatibility gate;
- a pre-existing DB without recognizable lineage is not treated as fresh;
- D4-B will use verified `before_migration` backup + consistent staged migration + atomic commit;
- migration staging must not use raw SQLite file copy;
- durable UpdateLog lives outside the working DB under launcher/startup ownership;
- interrupted `started` state is reconciled conservatively and never triggers blind destructive retry;
- previous package is not a generic rollback after DB commit;
- user-facing update state stays small and nontechnical;
- Restore remains closed.

## Authorization

```text
D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED
D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```
