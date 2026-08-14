# Progress

Updated: `2026-08-13`

## Closed baseline

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 is accepted and D4 is closed.
- CR-014 / ADR 0021 is accepted; the D5 guide/checklist implementation is present in this changeset and remains not lifecycle-closed.
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
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — IMPLEMENTED — NOT LIFECYCLE-CLOSED
D5 verification — AUTOMATED EXACT-PACKAGE + HUMAN CLEAN-MAC/CLEAN-PROFILE EVIDENCE REQUIRED
D5 lifecycle closure — NOT COMPLETED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED
```

## D4 closure

D4-A/B/C remain closed. D4-D final exact-package verification passed on `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881`; D4 is now lifecycle-closed.

D5 documentation/checklist implementation is ready for verification. Merge/closure still require external automated exact-package evidence plus a human clean-Mac/clean-profile rehearsal of the same exact artifact; Phase 12 and product release readiness remain gated.
