# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-13`

For historical pre-D4 decision state, see `docs/history/d4-pre-decision/`. The exact pre-decision `docs/current-lifecycle.md` is preserved there byte-identically from base `dc2301f7d4e101ad0fba851325dae9274f02da0c`.

## Authority

- ADR 0016 remains authoritative for destructive Restore.
- ADR 0018 remains authoritative for Restore interaction/validation session semantics.
- ADR 0019 remains authoritative for the bounded D3 macOS package decision.
- ADR 0020 is authoritative for D4 Update Safety.
- `docs/roadmap.md` remains the product-scope source for D4 and D5.
- `docs/domain-model-d4-update-safety.md` is the bounded D4 companion clarification.

## Current lifecycle

```text
PR #193 — MERGED — C4-III RESTORE LIFECYCLE CLOSURE
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED

CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
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

## D4-A closure truth

D4-A implements only the first ADR 0020 slice:

```text
resolve one effective application version
→ inspect canonical database lineage read-only
→ fresh/current/supported-older classification
→ fail closed on incompatible existing lineage
→ only then enter the pre-existing startup backup/migration path
```

Version identity:

- `backend/VERSION` is the one editable build-time product-version source;
- `backend/pyproject.toml` declares its version dynamically from `VERSION`;
- `scripts/package_macos.sh` reads the same source and generates `Info.plist` and `package-runtime.json` projections;
- `scripts/verify_product_version.py` rejects a package whose projections diverge;
- packaged backend runtime reads `package-runtime.json`; source runtime reads `backend/VERSION`;
- Settings/status receives the same effective runtime value;
- the database `app.version` placeholder remains historical and non-authoritative.

Schema compatibility:

- the existing backend migration-lineage classifier remains the one classifier;
- D4-A adds a path-level startup wrapper that opens the canonical DB read-only and calls that classifier;
- only a truly absent canonical path is `fresh`; a dangling symlink, non-file, missing migration history, newer schema, unknown/reordered/skipped history or unreadable DB fails closed;
- `pending_migration_ids()` is no longer used to decide ordinary startup compatibility before the gate;
- supported older lineage still uses the existing direct backup + migration execution after the gate. Replacing that execution with staged migration is D4-B and is not implemented here.

D4-A is merged and exact-head verified. D4-B is implemented in the current changeset, but exact-head verification and lifecycle closure are still pending; D4-C remains unauthorized.

## D4-A closure evidence

- implementation PR #195 merged as `45c052ed0421fc011e3e91c33822ff4075c668a0`;
- corrective/verification PR #196 exact verified head: `f294b15365fcf651790e2dc5638ed1551f616c3d`;
- PR #196 merged as `89dd69dc1958e622146e01869cc34d4cd2ec859e`;
- verified PR head and merge commit are content-identical (`0` changed files);
- external exact merged-head verifier run `31699624984`: PASS;
- evidence artifact `9180924875`, digest `sha256:b2ac042fa2f6d239aebae931e1c93aa81a9b8b7e3c6b2b6a45304e0d113d7993`.

## D4-B implementation truth

For a supported older canonical database, ordinary user-mode startup now follows the ADR 0020 staged path:

```text
read-only D4-A compatibility preflight
→ reconcile any durable interrupted started operation
→ create + verify before_migration backup
→ create consistent runner-owned stage
→ migrate stage only
→ verify stage target lineage
→ prove canonical unchanged during staging
→ atomically publish stage as canonical
→ verify canonical target lineage
→ durably record completed update
→ continue ordinary post-migration startup
```

`update-journal.json` is external startup-owned metadata under the user-data boundary, not inside the working SQLite database or package. The first D4 operation may record `from_app_version = null` because no trusted previous D4 update record exists; legacy mutable database `app.version` is never promoted into authority.

D4-B is **implementation-complete only in this changeset**. It is not lifecycle-closed, D4-C is not authorized, and exact-head + exact-package verification remain mandatory before any next-slice authorization.

## Closed Restore boundary

Restore remains closed. D4-A changes no protected Restore production blob, no Restore state machine, picker, source proof, control plane, backend handshake, replacement or recovery semantics.

## Release boundary

D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain outside CR-013/D4-A.
