# Progress

Updated: `2026-08-13`

## Closed baseline

- C4-III exact-head and exact-package verification passed and the Restore lifecycle is closed.
- Restore is `IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`.
- D3 macOS package MVP is implemented.
- CR-013 / ADR 0020 is accepted.
- Product release readiness is not claimed.

The exact pre-CR-013 progress file is preserved in `docs/history/d4-pre-decision/progress.md`.

## D4-A implementation

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

Focused authored checks include Python/shell syntax, source/package version resolution, package projection mismatch refusal and read-only startup wrapper behavior. Full repository exact-head verification remains the closure gate.

## Authorization

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```
