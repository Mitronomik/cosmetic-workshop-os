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
D5 — Remote install checklist — IMPLEMENTED — NOT LIFECYCLE-CLOSED
D5 verification — AUTOMATED EXACT-PACKAGE + HUMAN CLEAN-MAC/CLEAN-PROFILE EVIDENCE REQUIRED
D5 lifecycle closure — NOT COMPLETED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED
```

## Current task

**Verify the exact D5 implementation head; do not merge it without both evidence layers.**

The D5 guide/checklist is implemented by the current changeset without runtime changes. Required next actions are: external automated exact-package verification of the exact head/artifact, then a human Finder/System Settings rehearsal on a clean Mac or clean macOS user profile using that same exact artifact. Final PASS/DONE is recorded only by a later lifecycle-only closure changeset.

Do not modify backend/frontend/launcher/migrations/package runtime under D5. If rehearsal finds a product defect, stop and authorize/fix it separately. Do not start signing/notarization, DMG/PKG, public release hosting, GitHub Releases, auto-update/download, release channels, MDM/remote-management integration, Phase 12, product release readiness claims or Restore changes.

## Final D4 evidence

- exact tested main/head: `ec88b09193c8ed041e17daef3e3ffc0193d1b559`;
- D4-D run: `31751386881`; artifact `9201217317`; digest `sha256:0dc707f8823eb69934a5bc3b3b6824557533bafa3e1e86a7f13fc29c19a1af7d`;
- final result: `PASS — FULL AUTOMATED SMOKE PASSED`.
