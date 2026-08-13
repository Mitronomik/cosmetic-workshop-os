# Current focus

Updated: `2026-08-13`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Implement D4-C only, in a separate bounded PR.**

D4-A and D4-B are closed. D4-C may add only human-facing update status and bounded packaged failure UX on top of the existing startup-owned truth. It must not create a technical update admin dashboard or move update authority into the browser.

## D4-B closure evidence

- verified PR head: `8688fa3dba87205b4b4626ebab2902262fd4cd24`; run `31716610699`; artifact `9187785415`;
- merged head/current main: `d60a3be993c76b59292cf27ee66bcbe856669fc4`; run `31717705331`; artifact `9188228739`;
- verified-head → merged-head compare: `0` changed files;
- both Level-5 reports ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## Do not start

- D4-D exact-package closure;
- D5;
- auto-update/download;
- signing/notarization/DMG/App Store;
- release readiness;
- Restore changes.

Normative decision: `docs/decisions/0020-d4-update-safety-contract.md`.
