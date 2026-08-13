# Change requests

Updated: `2026-08-13`

The exact pre-CR-013 ledger is preserved in `docs/history/d4-pre-decision/change-requests.md`.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED — IMPLEMENTATION COMPLETED BY D3**.

Durable decision: `docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`.

CR-012 did not authorize D4, D5, signing, notarization, DMG, updater/download, App Store or release readiness.

## CR-013 — D4 Update Safety contract and bounded implementation authorization

Status: **ACCEPTED**.

Durable decision: `docs/decisions/0020-d4-update-safety-contract.md`.

Decision:

- D4 uses one app-version authority and ordered migration lineage as schema authority;
- ordinary startup must reject newer/unsupported existing lineage before mutation;
- D4-B architecture is staged migration + verified atomic commit, not in-place migration;
- staging and backup use SQLite-consistent snapshot semantics, never raw DB copy;
- UpdateLog durable truth is external to the working DB so migration failure cannot erase it;
- interrupted updates reconcile conservatively with no blind destructive retry;
- previous package is not a generic rollback after the DB commit point;
- Restore remains lifecycle-closed and unchanged.

Authorization:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — AUTHORIZED — IMPLEMENTATION NOT STARTED
D4-A — Version identity and compatibility preflight — AUTHORIZED NEXT — NOT IMPLEMENTED
D4-B — Safe migration execution and durable UpdateLog — PLANNED — NOT AUTHORIZED UNTIL D4-A IS MERGED AND VERIFIED
D4-C — User-facing update status and packaged failure UX — PLANNED — NOT AUTHORIZED UNTIL D4-B IS MERGED AND VERIFIED
D4-D — Exact-package update verification and D4 lifecycle closure — PLANNED — NOT AUTHORIZED UNTIL D4-C IS MERGED AND VERIFIED
D5 — Remote install checklist — NOT AUTHORIZED BY CR-013
Product release readiness — NOT CLAIMED
```

D4-A is the **only** newly authorized runtime slice.
