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
D5 — Remote install checklist — BLOCKED — PRODUCT DEFECT CONFIRMED IN HUMAN REHEARSAL
CR-015 — ACCEPTED — NATIVE MACOS APPLICATION LIFECYCLE BLOCKER FIX
D5 blocker fix — Native macOS application lifecycle — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — BLOCKED UNTIL FIX + FRESH EXACT-PACKAGE/HUMAN REHEARSAL
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014/CR-015
Product release readiness — NOT CLAIMED
```

## Current task

**Implement only the CR-015 native macOS application lifecycle blocker fix.**

A clean-Mac human D5 rehearsal confirmed that the current packaged `.app` can start and serve the browser UI, but it does not behave as a healthy native macOS application lifecycle owner: the Dock reports the app as not responding, ordinary Quit is not available as a reliable graceful shutdown path, and a subsequent Finder launch cannot be accepted as a verified restart. D5 closure is blocked.

CR-015 authorizes one bounded runtime repair: a minimal native AppKit lifecycle wrapper around the existing packaged bootstrap/launcher. The browser remains the product UI; backend/domain/data ownership does not move into the native wrapper. Do not modify business logic, database semantics, Restore semantics, D4 update semantics, frontend product flows or migrations except where a focused test harness must observe lifecycle behavior.

Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12 or product release readiness claims.

## Final D4 evidence

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- D4-D run: `31751386881`; artifact `9201217317`; digest `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.
