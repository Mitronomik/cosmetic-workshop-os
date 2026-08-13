# Change requests

Updated: `2026-08-13`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED — D4-A IMPLEMENTED; D4-A VERIFICATION/CLOSURE PENDING**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

D4-A has implemented the version-identity and compatibility-preflight slice only. It has not implemented staged migrations, durable UpdateLog, update UI/failure UX or exact-package D4 closure.

Authorization remains:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

D4-B is **not** authorized by implementation alone. D4-A must first merge, pass exact-head verification and be lifecycle-closed.
