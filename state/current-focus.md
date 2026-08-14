# Current focus

Updated: `2026-08-14`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — DONE — FINAL EXACT-PACKAGE VERIFICATION PASSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — BLOCKER FIXED — FRESH HUMAN REHEARSAL REQUIRED
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D5 verification — AUTOMATED BLOCKER FIX VERIFIED — FULL D5 PASS NOT YET CLAIMED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED
```

## Current task

**Repeat the D5 human clean-Mac/clean-profile rehearsal on the fixed exact package.**

CR-015 is implemented and verified. Runtime implementation head `d7f95141e5f41c7a806c3fafb71e942fe5892dd8` merged content-identically as `c38940349a80d345f3e833b61e4bf4e5e761c0eb` (`0` changed files from verified head to merge). External exact-package run `31780899805` proved LaunchServices start, macOS application-level Quit, complete packaged runtime/backend cleanup, released ports, LaunchServices restart and persistence using exact ZIP SHA-256 `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`.

No new runtime implementation slice is authorized now. Use the fixed exact package for the mandatory human D5 rehearsal. If the ordinary Finder/Dock/Quit/restart path fails again, stop and classify the new observation before changing code. If it passes, D5 still needs its documentation/checklist evidence and lifecycle closure; do not silently claim release readiness.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12 or product release readiness claims.

## Final D4 evidence

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- D4-D run: `31751386881`; artifact `9201217317`; digest `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.
