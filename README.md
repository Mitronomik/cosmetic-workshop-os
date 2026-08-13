# cosmetic-workshop-os

Local-first working system for a cosmetic workshop. Client-facing product name: **«Мастерская косметолога»**.

The product is a packaged local application, not a repository/admin panel. User data lives outside application code/package, ordinary product work is API-first, and critical business logic remains backend-owned.

## Current lifecycle

```text
PR #193 — MERGED — C4-III RESTORE LIFECYCLE CLOSURE
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

Normative lifecycle: `docs/current-lifecycle.md`.
D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.

The exact pre-CR-013 README is preserved in `docs/history/d4-pre-decision/README.md`.

## D4-A implementation

D4-A establishes the pre-mutation safety gate without implementing D4-B migration execution:

- `backend/VERSION` is the one editable build-time product-version source;
- backend `pyproject.toml`, `Info.plist`, `package-runtime.json` and Settings/status are projections of that identity;
- packaged runtime resolves version from its validated manifest projection; source runtime resolves the repository source;
- ordinary startup classifies the canonical SQLite database read-only before directory creation, backup or migration;
- only an absent canonical DB is fresh;
- current lineage continues normally, supported older lineage keeps the existing backup-before-migration path, and newer/unsupported/unreadable lineage fails closed;
- no protected Restore production file changes.

D4-B/C/D remain gated until D4-A is merged, exact-head verified and lifecycle-closed.

## Core product invariants

- local-first on a MacBook without mandatory internet;
- user data separate from code/package;
- API-first backend even for local operation;
- critical calculations and mutations in backend domain services;
- recipe versions and first-class client recipes;
- lot/movement-based inventory;
- transactional production;
- import through draft/preview/validation/confirmation;
- backup before migration;
- nontechnical user-facing UI;
- no silent mutation of historical data.

## Development authority

Read `AGENTS.md`, `docs/current-lifecycle.md`, relevant ADRs and the focused product/domain/test docs before changing behavior. Current D4 work must follow ADR 0020 and must not reopen the closed Restore boundary.
