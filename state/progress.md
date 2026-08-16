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
D5 — Remote install checklist — PILOT OPERATOR-ASSISTED PATH AUTHORIZED — FULL D5 PASS NOT CLAIMED
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
CR-016 — ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL
CR-017 — ACCEPTED — SINGLE-CLIENT OPERATOR-ASSISTED INSTALL/UPDATE CONTRACT
D5 pilot deployment — OPERATOR-ASSISTED PATH AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — CR-016 FAIL RECORDED; OPERATOR-ASSISTED REHEARSAL NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015/CR-016/CR-017
Product release readiness — NOT CLAIMED
```

## D4 closure

D4-A/B/C remain closed. D4-D final exact-package verification passed on `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881`; D4 is now lifecycle-closed.

CR-014 authorizes D5 only as documentation + exact-package assisted-install rehearsal. D5 is not implemented or verified yet; Phase 12 and product release readiness remain gated.

## CR-015 blocker decision

The clean-Mac D5 human rehearsal exposed `FAIL — PRODUCT` at ordinary application shutdown/restart. CR-015 / ADR 0022 authorizes the bounded native AppKit lifecycle repair next. D5 remains blocked and no release-readiness claim is permitted.

## CR-015 implementation closure

CR-015 blocker fix is merged and verified. Verified head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8` → merge `c38940349a80d345f3e833b61e4bf4e5e761c0eb` changed `0` files. Run `31780899805` passed `2692 passed, 1 skipped`, native package identity, LaunchServices start, application-level Quit/cleanup, restart persistence and second Quit. Exact ZIP SHA-256 `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`. D5 full PASS remains unclaimed pending fresh human rehearsal.


## CR-017 pilot distribution boundary

The CR-016 self-running downloaded `.command` experiment failed the mandatory human Finder rehearsal because Gatekeeper blocked the bootstrap before execution. CR-017 therefore authorizes only a single-client **operator-assisted** install/update pilot: a qualified support operator may use Terminal to verify the exact package and remove quarantine only from the verified staged `.app`; the client does not type commands. Gatekeeper remains globally enabled. No public/self-service distribution, signing/notarization, Phase 12 or release-readiness claim is created.
