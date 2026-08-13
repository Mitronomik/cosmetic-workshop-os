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
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED

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

D4-A, D4-B and D4-C are closed. D4-D is the only authorized next slice.

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

## D4-C closure truth

D4-C is **DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED**. Its implementation remains presentation-only over the D4-B startup authority: bounded read-only Settings status, exactly two packaged update-failure outcomes, no browser update authority, no raw update metadata and no protected Restore changes.

## D4-C closure evidence

- verified PR head: `ba577f1151e041c11019525862d9bb76eeb1404e`;
- PR-head Level-5 verifier: run `31747841343`, artifact `9199930504`, digest `sha256:a034cf7daa3416c18e73bec328f4c1d78adce240213ceff0ccef47be969f3de3`;
- merged head/current main: `3d69df192b5bdff9c7df067d8c8fde40154ebac9`;
- verified PR head → merge compare: `0` changed files;
- merged-head Level-5 verifier: run `31749503618`, artifact `9200580412`, digest `sha256:02f93910e6a6b1e1390c9782d89af320a244d1f6cb379bb5496a0c8e11dd8f78`;
- both trustworthy exact-package runs ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## D4-D authorization boundary

D4-D alone is **AUTHORIZED NEXT — NOT IMPLEMENTED**. It may perform the final exact-package D4 verification and D4 lifecycle closure required by ADR 0020. It may not introduce new update runtime authority, downloader/checking, D5, signing, notarization, DMG, App Store, release channels/readiness, cloud sync or Restore changes.

## Closed Restore boundary

Restore remains closed. D4-C changes no protected Restore production blob, no Restore state machine, picker, source proof, control plane, backend handshake, replacement or recovery semantics.

## Release boundary

D5, auto-update/download, GitHub Releases integration, signing, notarization, DMG, App Store, release channels and release readiness remain outside CR-013/D4-A.
