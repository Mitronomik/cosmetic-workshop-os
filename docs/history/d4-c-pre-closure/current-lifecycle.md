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
D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
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
- D4-A itself originally stopped at the compatibility gate; the now-closed D4-B slice replaces the supported-older direct migration seam with staged migration after that gate.

D4-A and D4-B remain closed. D4-C is implemented in the current branch; exact-head/exact-package verification and lifecycle closure remain pending, and D4-D remains unauthorized.

## D4-A closure evidence

- implementation PR #195 merged as `45c052ed0421fc011e3e91c33822ff4075c668a0`;
- corrective/verification PR #196 exact verified head: `f294b15365fcf651790e2dc5638ed1551f616c3d`;
- PR #196 merged as `89dd69dc1958e622146e01869cc34d4cd2ec859e`;
- verified PR head and merge commit are content-identical (`0` changed files);
- external exact merged-head verifier run `31699624984`: PASS;
- evidence artifact `9180924875`, digest `sha256:b2ac042fa2f6d239aebae931e1c93aa81a9b8b7e3c6b2b6a45304e0d113d7993`.

## D4-B closure truth

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

`update-journal.json` is external startup-owned metadata under the user-data boundary, not inside the working SQLite database or package. D4-B records `from_app_version = null` because it cannot prove the immediately previous package version: a previous completed update identifies the last migration-producing app, not necessarily the last app that ran. Legacy mutable database `app.version` and SemVer inference are never promoted into authority.

D4-B is **DONE — MERGED AND VERIFIED**. Its accepted Level-5 evidence remains authoritative; D4-C adds presentation only and does not change D4-B migration semantics.

## D4-B closure evidence

- verified implementation head: `8688fa3dba87205b4b4626ebab2902262fd4cd24`;
- PR-head Level-5 verifier: run `31716610699`, artifact `9187785415`, digest `sha256:fbbaa56a173929f41e18aa49adad40854210806433de2309052cffda8a4c7012`;
- merge/current main: `d60a3be993c76b59292cf27ee66bcbe856669fc4`; verified-head → merge compare: `0` changed files;
- merged-head Level-5 verifier: run `31717705331`, artifact `9188228739`, digest `sha256:2a3e615e504e6c047b8f1b45690f3595a0ef4bb71dcd1d9fadf669ecd64af415`;
- both runs ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## D4-C implementation truth

Implementation code commit: `adfe37a3f68a545635f173c22d4710eacde86e74`.

D4-C projects D4-B startup truth into a bounded read-only Settings status and two fixed packaged failure outcomes. It exposes no raw update metadata, paths or tracebacks and creates no browser update command. The before-commit outcome claims only that canonical DB replacement did not occur; the uncertain outcome makes no rollback/data-unchanged claim. Closed Restore production blobs remain unchanged.

D4-C is **IMPLEMENTED — VERIFICATION PENDING**, not lifecycle-closed.

## D4-C verification boundary

The exact published PR head still requires full regression, lifecycle integrity, frontend build, real macOS package and exact-package D4-C smoke. D4-D, D5, release/distribution work and Restore changes remain unauthorized.

## Closed Restore boundary

Restore remains closed. D4-C changes no protected Restore production blob, no Restore state machine, picker, source proof, control plane, backend handshake, replacement or recovery semantics.

## Release boundary

D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain outside CR-013/D4-A.
