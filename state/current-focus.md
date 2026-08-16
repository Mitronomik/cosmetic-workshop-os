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

## Current task

**Implement only CR-017 — Single-client operator-assisted install/update after this decision merges.**

CR-016 implementation head `0179be9fa1758a47662f86c5a14a7f24341815c5` and automated run `31959318870` remain historical evidence only. The clean-Mac human rehearsal proved the downloaded `.command` cannot bootstrap itself because Gatekeeper blocks it before execution; PR #210 is closed without merge.

CR-017 authorizes a support operator Terminal workflow only. The operator verifies exact package SHA-256 and app identity before removing quarantine from the verified staged `.app`. The client never types commands. Gatekeeper stays globally enabled, no `sudo` is permitted, and product database/user-data/D4/Restore/runtime semantics remain untouched.

After the operator-assisted implementation is separately verified, repeat the clean-Mac D5 rehearsal using that operator procedure. Full D5 PASS, Phase 12 and product release readiness remain unclaimed.

## Prior CR-015 handoff truth

The CR-015 closure correctly recorded: **Repeat the D5 human clean-Mac/clean-profile rehearsal on the fixed exact package** and **No new runtime implementation slice is authorized now**. Those statements remain true for product runtime scope. CR-016 is a later, separate distribution/support decision and authorizes only the bounded packaging/bootstrap exception from ADR 0023; it does not reopen runtime, backend, frontend, database, Restore or D4 semantics.

## CR-015 evidence retained

- verified implementation head: `d7f95141e5f41c7a806c3fafb71e942fe5892dd8`;
- content-identical merge: `c38940349a80d345f3e833b61e4bf4e5e761c0eb`;
- external exact-package run: `31780899805`;
- exact fixed ZIP SHA-256: `85f993a93082c4b3a36771318cf8c0c3abf02be56b1374a32a62d1a6b9279ee6`.

## Final D4 evidence

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- D4-D run: `31751386881`; artifact `9201217317`; digest `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.
