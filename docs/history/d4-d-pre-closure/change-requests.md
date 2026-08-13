# Change requests

Updated: `2026-08-13`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED — D4-A/B/C CLOSED; D4-D AUTHORIZED NEXT**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

D4-A, D4-B and D4-C are closed. D4-C verified PR head `ba577f1151e041c11019525862d9bb76eeb1404e` and merged head `3d69df192b5bdff9c7df067d8c8fde40154ebac9` passed Level-5 exact-package verification and are content-identical. D4-D alone is authorized next.

Authorization remains:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-A DONE; D4-B DONE; D4-C DONE; D4-D AUTHORIZED NEXT
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-C — User-facing update status and packaged failure UX — DONE — MERGED AND EXACT-HEAD/EXACT-PACKAGE VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

D4-A/B/C closure remains satisfied. D4-D only is authorized next; D5 and release readiness remain unauthorized/not claimed.
