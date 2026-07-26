# Current focus — B3.6 Order-to-production shared-feedback lifecycle

- B3.4+B3.5 is DONE: PR #137 merged at `10e985229e8020fcf98c67427cde889b5cd934f8`.
- PR #138 is open and non-draft on `codex/b3.6-order-production-feedback`.
- Exact starting `main` SHA: `10e985229e8020fcf98c67427cde889b5cd934f8`.
- Published head before the current correction: `32cec36fa40ae2db4001af1e0d0b60e965bc3c77`.
- Exact-head review found that a second uncertain production for another Order could replace the first unresolved production reconciliation obligation.
- The correction is being made in the same PR with a global production lock while the original exact reconciliation obligation remains unresolved.
- Runtime scope: `/orders` route ownership; list/reference/detail reads; create/update; cancel/archive; readiness; Production Confirmation; exactly one production POST; production-history handoff; exact original-Order GET-only reconciliation.
- Safety boundary: stale, wrong-Order, invalid and detached callbacks cannot present, announce, move focus, or clear a reconciliation obligation. Accepted requests settle busy state exactly once; rejected starts send no request.
- Backend production code, APIs, persistence, schema, migrations, dependencies, and lockfiles remain unchanged.
- Completed verification: focused Order frontend suites pass twice; all required frontend regressions and build pass; focused backend 95/95; complete backend 496 collected, 492 passed, the same 4 accepted failures, 0 skipped; branch-only failure delta 0.
- B3.6 is not DONE and remains under exact-head review in PR #138.
- Smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Next gate: publish this correction to PR #138, review the corrected exact head, then run the separately authorized full Block B exact-head integration smoke.
