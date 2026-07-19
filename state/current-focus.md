# Current focus

## Goal

A3.9 — Production Confirmation structured errors and mutation safety for PR #124. Keep the existing Production Confirmation runtime slice safe, understandable, recoverable, transactional, and resistant to duplicate/stale/conflicting execution.

PR #124 is the active A3.9 Draft PR on managed branch `codex-l6nqu0`. Reviewed published head `8ee85e2baff18e278da945a4d89634c5db9335f8` requires correction. Exact base: `c6d87df635a5cf7d063b43ffc16dc02d64e08103`.

## Allowed scope/files

- Backend Production Confirmation endpoint/service and focused tests.
- Existing frontend Orders Production Confirmation lifecycle/presentation helpers and dependency-free tests.
- Directly affected API/project-state documentation.

## Non-goals

- No FEFO, density, recipe, readiness-calculation, cost/tax/margin, schema, migration, dependency, CI, responsive table containment, partial production, production undo/rollback UI, unrelated route, or A4 work.

## Tests

Required corrective checks: focused frontend lifecycle/presentation tests, frontend build, focused backend Production Confirmation tests, readiness/orders backend tests, full backend suite with exact-base comparison, `git diff --check`, and repository cleanliness.

## Acceptance criteria

- Production errors remain visible after readiness invalidation.
- Structured backend detail is consumed safely, including `next_action`.
- Uncertain outcomes have an explicit authoritative Order/ProductionBatch reconciliation path.
- Authoritative Order A success or uncertainty remains attached to A after navigating to B.
- Success plus failed refresh remains success.
- No blind duplicate production is possible.
- Focus anchors exist for confirmation, failure/recovery, and success states.
- Rollback tests prove no partial database mutation, status/timestamp mutation, or audit entry survives injected failures.

## Current evidence state

A3.8 is DONE: PR #123 is merged; accepted exact-head-smoked runtime head `34eeaf11dbe7fbfabb3bd36ad8aa79b9469892f5`; local merge/base commit `c6d87df635a5cf7d063b43ffc16dc02d64e08103`; final A3.8 exact-head smoke `PASS — FULL AUTOMATED SMOKE PASSED` was external local evidence, not GitHub Actions.

A3.9 remains IN PROGRESS. Exact-head production browser smoke has not yet been run and must wait until this corrective head passes human code review. A4 remains separate.
