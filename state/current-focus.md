# Current focus — B3.6 Order-to-production shared-feedback lifecycle

- B3.4+B3.5 is DONE: PR #137 merged at `10e985229e8020fcf98c67427cde889b5cd934f8`.
- B3.6 is the active slice. PR #138 is open and non-draft on branch `codex/b3.6-order-production-feedback`.
- Exact starting `main` SHA: `10e985229e8020fcf98c67427cde889b5cd934f8`.
- Current reviewed runtime head before this documentation commit: `a02d5a89f56421ab55f3d75c2ef4699a6a4946a2`.
- Published correction commit: `a02d5a8 Prevent cross-order production reconciliation loss`.
- Exact-head review found a cross-Order production reconciliation collision; the published correction closes that blocker.
- Runtime scope: `/orders` route ownership; list/reference/detail reads; create/update; cancel/archive; readiness; Production Confirmation; exactly one production POST; production-history handoff; exact original-Order GET-only reconciliation.
- While any production reconciliation obligation is unresolved, Production Confirmation and production POST operations are globally blocked. Another Order cannot replace the originating obligation.
- Only coherent exact reconciliation of the originating Order and its exact ProductionBatch releases the production lock. Stale, wrong-Order, invalid, partial, mismatched, or detached reads cannot unlock it.
- Backend production semantics, APIs, persistence, schema, migrations, dependencies, and lockfiles remain unchanged.
- Implementation and blocker correction are published and reviewed; this documentation commit aligns project memory with that runtime state.
- B3.6 is not DONE before the full Block B exact-head integration smoke.
- Smoke status: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
- Next acceptance gate: run one full Block B integration smoke against the final exact head of PR #138 after this documentation commit. Do not merge before that smoke is reviewed.
