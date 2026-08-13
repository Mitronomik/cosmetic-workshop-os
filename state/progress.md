# Progress

Updated: `2026-08-13`

## Closed baseline

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 is accepted.
- Product release readiness is not claimed.

The exact pre-CR-013 progress file is preserved in `docs/history/d4-pre-decision/progress.md`.

## D4-A closure

Implemented in the current D4-A changeset:

- canonical `backend/VERSION` product-version source;
- backend pyproject dynamic projection from that source;
- package build projection into Info.plist and package-runtime.json;
- package projection verifier;
- source/package effective runtime resolver;
- Settings/status effective version projection;
- `app.db.startup_compatibility` read-only canonical-DB classifier wrapping the existing `app.db.migration_lineage` authority;
- startup ordering changed so version + compatibility resolve before user-directory creation, backup or migration;
- `pending_migration_ids()` is no longer the ordinary-startup compatibility decision;
- newer/unsupported/unreadable pre-existing databases fail closed without reaching backup or migration;
- no protected Restore production file changed.

D4-A exact merged-head verification passed on `89dd69dc1958e622146e01869cc34d4cd2ec859e` in external run `31699624984`; full regression, lifecycle checker, frontend build, real macOS package, exact-package version identity, newer-schema fail-closed safety and clean postflight all passed. Evidence artifact: `9180924875`.

## Authorization

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## D4-B implementation pending verification

The current D4-B changeset implements staged migration, verified `before_migration` backup, atomic canonical publication, durable external UpdateLog and conservative interruption reconciliation. Full exact-head and exact-package verification are still required before lifecycle closure.

D4-C/D, D5 and release readiness remain gated.
