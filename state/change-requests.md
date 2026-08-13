# Change requests

Updated: `2026-08-13`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED — D4-A/B CLOSED; D4-C IMPLEMENTED, VERIFICATION PENDING**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

D4-A and D4-B are closed. D4-C implementation code commit `adfe37a3f68a545635f173c22d4710eacde86e74` adds only the bounded read-only status and packaged failure UX authorized by CR-013. D4-C is not yet exact-head/exact-package verified or lifecycle-closed; D4-D remains unauthorized.

Authorization remains:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-C IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

D4-A and D4-B closure remain satisfied. D4-C is implementation-complete in the current branch; only D4-C verification and lifecycle closure are authorized next. D4-D is not authorized.
