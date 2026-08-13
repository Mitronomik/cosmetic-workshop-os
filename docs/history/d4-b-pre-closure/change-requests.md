# Change requests

Updated: `2026-08-13`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED — D4-A CLOSED; D4-B IMPLEMENTED, VERIFICATION PENDING**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

D4-A remains closed. The current D4-B changeset implements staged migrations, verified backup, atomic canonical publication, durable external UpdateLog and interruption reconciliation. It does not implement D4-C update UI/failure UX or D4-D lifecycle closure.

Authorization remains:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — IN PROGRESS — D4-B IMPLEMENTED, VERIFICATION PENDING
D4-A — Version identity and compatibility preflight — DONE — MERGED AND EXACT-HEAD VERIFIED
D4-B — Safe migration execution and durable UpdateLog — IMPLEMENTED — EXACT-HEAD VERIFICATION AND LIFECYCLE CLOSURE PENDING
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

D4-A closure conditions are satisfied on merged head `89dd69dc1958e622146e01869cc34d4cd2ec859e`. D4-B implementation now requires exact-head verification, merge verification and separate lifecycle closure before D4-C can become authorized.
