# Change requests

Updated: `2026-08-16`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED — D4 CLOSED; NO D5 AUTHORIZATION**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

D4-A/B/C remain closed. D4-D final exact-package verification passed on exact main `ec88b09193c8ed041e17daef3e3ffc0193d1b559` in run `31751386881`. D4 is lifecycle-closed; CR-013 provides no D5 authorization.

Authorization remains:

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

D4-A/B/C/D closure is satisfied. CR-013 itself authorizes no D5 work.

## CR-014 — D5 Remote Install Rehearsal contract

Status: **ACCEPTED — D5 AUTHORIZED NEXT; NOT IMPLEMENTED**.

Durable decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.

CR-014 defines D5 as documentation + exact-package assisted-install rehearsal on a clean Mac or clean macOS user profile. It authorizes no runtime change and no signing/notarization/DMG/PKG/App Store/public release/GitHub Releases/auto-update/release-channel/MDM/Phase-12 work. A full D5 PASS requires both automated exact-package evidence and a human non-technical Finder/System Settings rehearsal.

D5 is the only authorized next stage. Product release readiness remains not claimed.

## CR-015 — Native macOS application lifecycle blocker fix

Status: **ACCEPTED — IMPLEMENTED AND EXACT-PACKAGE VERIFIED**.

Durable decision: `docs/decisions/0022-native-macos-application-lifecycle.md`.

The mandatory D5 human rehearsal confirmed a product blocker: first launch and browser workflows worked, but the `.app` did not provide a healthy responsive native macOS lifecycle for ordinary Dock Quit and verified Finder restart. CR-015 authorizes only a minimal native AppKit lifecycle owner around the existing packaged bootstrap/launcher. It does not authorize business-logic changes, frontend redesign, database or migration changes, Restore/D4 semantic changes, signing, notarization, DMG/PKG, App Store, auto-update, public release hosting, MDM, Phase 12 or product release readiness.

### CR-015 implementation evidence

Implemented by verified head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8`, merged as `c38940349a80d345f3e833b61e4bf4e5e761c0eb` with `0` changed files. External exact-package run `31780899805` passed the complete application-level Quit/restart blocker matrix; exact ZIP SHA-256 `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`. CR-015 is closed as an implementation blocker fix. D5 itself remains open for fresh human rehearsal and final evidence.

## CR-016 — Single-client assisted install and update bootstrap

Status: **ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL**.

Durable decision: `docs/decisions/0023-single-client-assisted-install-bootstrap.md`.

The clean-Mac rehearsal exposed a second distribution blocker: the unsigned/unnotarized exact package can be rejected by Gatekeeper before product code runs. For the current single known client, paying for Developer ID/notarization is not presently justified and the product architecture must not be rolled back or redesigned.

CR-016 authorizes only a version-specific assisted bootstrap delivered as an outer ZIP containing the canonical exact `CosmeticWorkshopOS-mac.zip` plus a double-clickable `.command`. The bootstrap must verify the exact companion ZIP SHA-256 and staged bundle identity before any quarantine metadata is removed. Only the verified staged `CosmeticWorkshopOS.app` may have `com.apple.quarantine` removed. Gatekeeper must remain enabled globally.

The same bounded bootstrap may handle first installation and later manual package replacement for this one-client pilot. It must install in the user's application space without `sudo`, retain the previous `.app` before update publication, never touch the database or user-data directory, and leave all schema compatibility/backup/migration/UpdateLog semantics to the already-closed D4 implementation.

CR-016 does **not** authorize Developer ID, notarization, global Gatekeeper disable, SIP/Security Policy weakening, DMG/PKG, App Store, public release hosting, GitHub Releases, automatic update downloads, release channels, backend/frontend/domain changes, database/Restore changes, Phase 12 or product release readiness.

The implementation must be separately tested and followed by a human clean-Mac rehearsal of the actual downloaded outer ZIP and Finder double-click `.command` flow. Success proves only the bounded single-client assisted-install mode; it does not prove signed/notarized/public/self-service distribution readiness.


### CR-016 implementation outcome

Implementation head `0179be9fa1758a47662f86c5a14a7f24341815c5` passed automated post-execution run `31959318870`, but the mandatory clean-Mac Finder rehearsal produced `FAIL — PRODUCT`: Gatekeeper blocked the downloaded `.command` before execution. PR #210 was closed without merge. The self-running bootstrap model is rejected.

## CR-017 — Single-client operator-assisted install and update

Status: **ACCEPTED — BOUNDED IMPLEMENTATION AUTHORIZED AFTER DECISION MERGE**.

Durable decision: `docs/decisions/0024-single-client-operator-assisted-install.md`.

CR-017 replaces only the failed CR-016 bootstrap mechanism. A qualified support operator may use Terminal/screen sharing to verify the exact product package, remove quarantine only from the verified staged `.app`, install/update under the current user's application space, and launch it. The client never types commands and Gatekeeper remains globally enabled.

CR-017 does not authorize `sudo`, global Gatekeeper/SIP/security weakening, database/Restore/D4 changes, backend/frontend/domain changes, signing/notarization, public distribution, auto-update/download, Phase 12 or product release readiness. A clean-Mac operator-assisted rehearsal remains mandatory before any pilot PASS claim.
