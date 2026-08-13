# Handoff

Updated: `2026-08-13`

## Current authority

```text
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
D3 — macOS package MVP — IMPLEMENTED
```

- CR-013 / ADR 0020 decides D4 Update Safety.
- D4-A is DONE — merged and exact-head verified.
- D4-B is IMPLEMENTED — exact-head verification and lifecycle closure pending.

The exact pre-CR-013 handoff is preserved in `docs/history/d4-pre-decision/handoff.md`.

## Lifecycle

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

## D4-B implementation handoff

Load-bearing implementation seams:

1. `backend/VERSION` — only editable product-version authority.
2. `backend/app/version.py` — validates and resolves repository vs packaged effective version without version ordering.
3. `scripts/package_macos.sh` — generates package version projections from the authority.
4. `scripts/verify_product_version.py` — build-time projection consistency gate.
5. `backend/app/db/startup_compatibility.py` — opens existing canonical DB read-only and delegates lineage classification to `app.db.migration_lineage`.
6. `backend/app/services/startup.py` — runs version + schema preflight before directory creation, backup or migrations.
7. `backend/app/services/runtime_identity.py` + thin Settings route — expose the same effective version read-only.

Supported older schemas now enter `backend/app/services/update_safety.py` after the closed D4-A gate. That service owns verified backup, consistent stage creation, stage-only migration, target verification, atomic canonical publication and external UpdateLog reconciliation; current/fresh/development paths retain their bounded existing behavior.

If D4-B verification reveals a need to change a protected Restore production blob or authorize D4-C behavior, stop and open the appropriate separate decision/lifecycle step rather than widening this implementation PR.

Verification evidence: merged head `89dd69dc1958e622146e01869cc34d4cd2ec859e`, run `31699624984`, artifact `9180924875`.
