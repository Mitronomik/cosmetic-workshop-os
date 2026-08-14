# Change requests

Updated: `2026-08-13`

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
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED
```

D4-A/B/C/D closure is satisfied. CR-013 itself authorizes no D5 work.

## CR-014 — D5 Remote Install Rehearsal contract

Status: **ACCEPTED — D5 AUTHORIZED NEXT; NOT IMPLEMENTED**.

Durable decision: `docs/decisions/0021-d5-remote-install-rehearsal-contract.md`.

CR-014 defines D5 as documentation + exact-package assisted-install rehearsal on a clean Mac or clean macOS user profile. It authorizes no runtime change and no signing/notarization/DMG/PKG/App Store/public release/GitHub Releases/auto-update/release-channel/MDM/Phase-12 work. A full D5 PASS requires both automated exact-package evidence and a human non-technical Finder/System Settings rehearsal.

D5 is the only authorized next stage. Product release readiness remains not claimed.

## CR-015 — Native macOS application lifecycle blocker fix

Status: **ACCEPTED — BOUNDED FIX AUTHORIZED NEXT**.

Durable decision: `docs/decisions/0022-native-macos-application-lifecycle.md`.

The mandatory D5 human rehearsal confirmed a product blocker: first launch and browser workflows worked, but the `.app` did not provide a healthy responsive native macOS lifecycle for ordinary Dock Quit and verified Finder restart. CR-015 authorizes only a minimal native AppKit lifecycle owner around the existing packaged bootstrap/launcher. It does not authorize business-logic changes, frontend redesign, database or migration changes, Restore/D4 semantic changes, signing, notarization, DMG/PKG, App Store, auto-update, public release hosting, MDM, Phase 12 or product release readiness.
