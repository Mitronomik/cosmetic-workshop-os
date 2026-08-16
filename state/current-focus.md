# Current focus

Updated: `2026-08-16`

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

**Implement only CR-016 — Single-client assisted install and update bootstrap after the decision changeset merges.**

The clean-Mac rehearsal established that the remaining blocker is distribution trust for the unsigned/unnotarized package, not the product runtime. For the current single known client, ADR 0023 authorizes a bounded version-specific `.command` bootstrap instead of Developer ID/notarization or a product redesign.

Authorized implementation scope is only the packaging/support layer required to produce an outer ZIP containing the canonical exact `CosmeticWorkshopOS-mac.zip` plus `Установить или обновить Мастерскую.command`. The generated bootstrap must verify the companion ZIP SHA-256 and staged bundle identity first, then and only then remove quarantine from that verified staged `.app`, install it under the user's application space and support the same bounded flow for later manual updates.

Do not modify backend, frontend, domain logic, database/migrations, Restore or D4 update-safety semantics. Do not globally disable Gatekeeper, use `sudo`, weaken SIP/Security Policy, add signing/notarization, add automatic update downloads, public distribution, release channels, Phase 12 or product release-readiness claims.

The implementation must remain fail-closed and must be followed by a human clean-Mac rehearsal of the actual downloaded outer ZIP and Finder double-click `.command` flow. Direct shell execution in CI is not a substitute for that human handoff.

## CR-015 evidence retained

- verified implementation head: `d7f95141e5f41c7a806c3fafb71e942fe5892dd8`;
- content-identical merge: `c38940349a80d345f3e833b61e4bf4e5e761c0eb`;
- external exact-package run: `31780899805`;
- exact fixed ZIP SHA-256: `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`.

## Final D4 evidence

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- D4-D run: `31751386881`; artifact `9201217317`; digest `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.
