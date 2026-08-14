# Progress

Updated: `2026-08-13`

## Closed baseline

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 is accepted and D4 is closed.
- CR-014 / ADR 0021 is accepted; D5 alone is authorized next.
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
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED
```

## D4 closure

D4-A/B/C remain closed. D4-D final exact-package verification passed on `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881`; D4 is now lifecycle-closed.

CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal. D5 is not implemented or verified yet; Phase 12 and product release readiness remain gated.

## CR-015 blocker decision

The clean-Mac D5 human rehearsal exposed `FAIL — PRODUCT` at ordinary application shutdown/restart. CR-015 / ADR 0022 authorizes the bounded native AppKit lifecycle repair next. D5 remains blocked and no release-readiness claim is permitted.
