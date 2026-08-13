# Current focus

Updated: `2026-08-14`

## Current lifecycle

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

## Current task

**Execute D4-D only, in a separate bounded PR.**

D4-D owns final exact-package verification of the complete D4 manual-update safety contract and D4 lifecycle closure. It must not create a downloader/updater, new update authority, technical admin UI, release/distribution work or Restore changes.

## D4-C accepted evidence

- verified PR head: `ba577f1151e041c11019525862d9bb76eeb1404e`; run `31747841343`; artifact `9199930504`;
- merged head/current main: `3d69df192b5bdff9c7df067d8c8fde40154ebac9`; run `31749503618`; artifact `9200580412`;
- verified-head → merge compare: `0` changed files;
- both Level-5 reports ended `PASS — FULL AUTOMATED SMOKE PASSED`.

## Do not start

- D5;
- auto-update/download or internet update checking;
- signing/notarization/DMG/App Store/release channels;
- product release readiness claims;
- Restore changes.
