# Current focus — A3.8 Production Readiness feedback and lifecycle correction

## Goal

Close the human-review findings on Draft PR #123 while preserving the read-only Production Readiness boundary and the existing Order request-generation architecture.

Reviewed history: PR #123 exists and remains Draft/IN REVIEW. Reviewed published head `69da410bccfc7bf9c852ef5a807d039b4fa4a74d` passed exact-head browser smoke as external local evidence, not GitHub Actions evidence. Human review then found reverse mutual-exclusion, readiness-revision freshness, and persistent behavioral-test gaps, so A3.8 is not DONE.

## Allowed scope

- Existing Orders detail, Production Readiness presentation, and Production Confirmation guard only.
- Existing Order request-generation, context-invalidation, transient-owner, and per-order freshness architecture.
- Narrow same-Order exclusion between readiness and pending production/cancel/archive writes.
- Duplicate cancel/archive protection and generation-safe owner cleanup.
- Captured Order revision and operation generation at readiness request start.
- A small extracted readiness presentation module and deterministic DOM/view tests without a frontend framework or dependency change.
- Focused frontend lifecycle/presentation tests, existing backend readiness no-write regressions, and directly affected documentation/state.

## Non-goals

- No change to backend readiness calculations, FEFO, density conversion, inventory policy, cost, tax, margin, or eligibility rules.
- No change to Production Confirmation domain behavior, ingredient/packaging write-off, cancellation/archive domain rules, schemas, migrations, responsive tables, dependencies, CI, or unrelated routes.
- No generic global request manager and no A3.9 or A4 work.

## Tests

- Frontend form-validation, targeted-validation-update, Order mutation lifecycle, readiness presentation, and build checks; independent frontend scripts may run concurrently only when their generated output directories do not collide.
- Focused backend Production Readiness and Orders suites plus full backend comparison with exact base `8c4a092d055fd221cb18da901cee9e90106b33a4`.
- `git diff --check`, clean status, and critical diff review.
- A new corrective exact-published-head browser smoke with isolated data and exact readiness/production/cancel/archive request counts. The reviewed-head smoke cannot be reused for a corrective head.

## Acceptance criteria

- Readiness cannot start while production, cancel, or archive is pending for the same Order.
- Readiness blocks conflicting Order create/update, cancel/archive, reload, and Production Confirmation while it owns the current Order context.
- Duplicate cancel/archive actions produce one POST each; stale write callbacks cannot clear a newer owner.
- A readiness result uses the Order revision captured at request start and is current only when no conflicting Order mutation generation changed.
- Ready, warning, blocked, stale, loading, retryable system failure, escaping, and Production Confirmation eligibility have committed behavioral DOM/view coverage.
- Corrected exact-head smoke proves recovered controls, no duplicates, no unintended ProductionBatch/stock/status mutation, no unexpected page/console/backend errors, and remote/tested SHA equality.
- PR #123 stays Draft/IN REVIEW. A3.9 and A4 remain separate.
