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
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
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

D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice; D5 and release readiness remain gated.

D4-A closure evidence: verified PR head `f294b15365fcf651790e2dc5638ed1551f616c3d` merged as `89dd69dc1958e622146e01869cc34d4cd2ec859e`; exact merged-head verifier `31699624984` passed.

## D4-A/B/C closed baseline / D4-D next

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

## D4-C closed baseline / D4-D next

D4-C is merged, exact-head/exact-package verified and lifecycle-closed.

- verified PR head: `ba577f1151e041c11019525862d9bb76eeb1404e`; Level-5 run `31747841343`; artifact `9199930504`; digest `sha256:a034cf7daa3416c18e73bec328f4c1d78adce240213ceff0ccef47be969f3de3`;
- merged head: `3d69df192b5bdff9c7df067d8c8fde40154ebac9`; Level-5 run `31749503618`; artifact `9200580412`; digest `sha256:02f93910e6a6b1e1390c9782d89af320a244d1f6cb379bb5496a0c8e11dd8f78`;
- verified PR head → merge: `0` changed files;
- redacted Settings update status, fixed packaged update-failure outcomes and closed Restore protections are preserved.

D4-D is authorized next only for exact-package D4 verification and D4 lifecycle closure. D5 and product release readiness remain unauthorized/not claimed.

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
