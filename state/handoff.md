# Handoff

Updated: `2026-08-13`

## Current authority

- Restore is closed and unchanged.
- D3 package MVP is implemented.
- CR-013 / ADR 0020 decides D4 Update Safety.
- D4-A is implemented but not lifecycle-closed.
- D4-B remains unauthorized until D4-A is merged and exact-head verified.

The exact pre-CR-013 handoff is preserved in `docs/history/d4-pre-decision/handoff.md`.

## Lifecycle

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

## D4-A implementation handoff

Load-bearing implementation seams:

1. `backend/VERSION` — only editable product-version authority.
2. `backend/app/version.py` — validates and resolves repository vs packaged effective version without version ordering.
3. `scripts/package_macos.sh` — generates package version projections from the authority.
4. `scripts/verify_product_version.py` — build-time projection consistency gate.
5. `backend/app/db/startup_compatibility.py` — opens existing canonical DB read-only and delegates lineage classification to `app.db.migration_lineage`.
6. `backend/app/services/startup.py` — runs version + schema preflight before directory creation, backup or migrations.
7. `backend/app/services/runtime_identity.py` + thin Settings route — expose the same effective version read-only.

Supported older schemas intentionally still use the pre-existing direct backup/migration execution **after** the gate. That seam belongs to D4-B and must not be redesigned in D4-A.

If verification reveals a need to change a protected Restore production blob, stop and open a separate decision rather than widening D4-A.
