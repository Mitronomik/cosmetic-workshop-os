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
D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

Normative lifecycle: `docs/current-lifecycle.md`.
D4 decision: `docs/decisions/0020-d4-update-safety-contract.md`.

The exact pre-CR-013 README is preserved in `docs/history/d4-pre-decision/README.md`.

## D4-A closed baseline

D4-A establishes the pre-mutation safety gate without implementing D4-B migration execution:

- `backend/VERSION` is the one editable build-time product-version source;
- backend `pyproject.toml`, `Info.plist`, `package-runtime.json` and Settings/status are projections of that identity;
- packaged runtime resolves version from its validated manifest projection; source runtime resolves the repository source;
- ordinary startup classifies the canonical SQLite database read-only before directory creation, backup or migration;
- only an absent canonical DB is fresh;
- current lineage continues normally, supported older lineage keeps the existing backup-before-migration path, and newer/unsupported/unreadable lineage fails closed;
- no protected Restore production file changes.

D4-B remains closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure are still pending, and D4-D remains gated.

D4-A closure evidence: verified PR head `f294b15365fcf651790e2dc5638ed1551f616c3d` merged as `89dd69dc1958e622146e01869cc34d4cd2ec859e`; exact merged-head verifier `31699624984` passed.

## D4-B closed baseline / D4-C implementation

The current D4-B changeset replaces only the supported-older direct migration seam:

- `before_migration` backup remains the ADR 0015 SQLite Online Backup snapshot and is verified before staging;
- a runner-owned `.stage` snapshot is created beside the canonical DB with the same consistent SQLite primitive;
- migrations execute only against the stage;
- stage and target lineage are verified before atomic publication;
- the canonical DB is checked unchanged during staging and is replaced only at the commit point;
- durable `update-journal.json` lives outside the working DB and records `started/completed/failed`;
- interrupted `started` operations reconcile conservatively and never blindly resume a stage;
- stage cleanup requires deterministic operation ownership and removes runner-owned SQLite sidecars;
- D4-C is implemented separately as a read-only human-facing status projection plus bounded packaged failure presentation; D4-B remains the update authority.

D4-B closure evidence: verified PR head `8688fa3dba87205b4b4626ebab2902262fd4cd24`, PR-head Level-5 run `31716610699`; merged head `d60a3be993c76b59292cf27ee66bcbe856669fc4`, merged-head Level-5 run `31717705331`. Both exact-package runs passed and the verified PR head is content-identical to the merge commit.

## D4-C implementation pending verification

Implementation code commit: `adfe37a3f68a545635f173c22d4710eacde86e74`.

D4-C adds a redacted read-only Settings update status and exactly two fixed packaged update-failure outcomes. Browser-visible data excludes operation/schema/stage/backup identities, raw failure categories, paths and tracebacks. There is no update command or technical update console. Protected Restore blobs remain unchanged.

D4-D remains unauthorized until D4-C is merged, verified and lifecycle-closed.

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
