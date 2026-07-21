# Current focus

## Baseline

PR #132 is DONE. It merged as `2ce5a4d7ba099603b733e7f2836f417da0614605` (`Merge pull request #132 from Mitronomik/codex/repair-focused-frontend-test-scripts`) and completed the focused frontend TypeScript test-compilation hardening. Focused frontend suites now compile their intended source modules with repository-local `tsc -p` configs, emit only under `frontend/dist-tests/`, and clean stale output before each run.

The B1/B2 diagnostic audit remains authoritative: no demo-fixture correction is required, no backend Dashboard read-model correction is required, demo installation is explicit, duplicate demo installation is rejected safely, alert regeneration and purchase-suggestion regeneration are stable, operational source data is meaningful, and passive source reads do not mutate business data.

B2 browser presentation evidence is not marked complete here unless the B3.1 exact published-head smoke passes.

## Active task

**B3.1 — Shared feedback for Dashboard and Onboarding** is active on the current branch.

Scope is limited to:

- `/` Dashboard load/manual refresh feedback and stale-data lifecycle;
- the onboarding workspace rendered on Dashboard for start, complete step, skip, and reset mutations;
- passive regression coverage for `/help`.

Backend endpoints, backend data models, migrations, demo fixtures, alert generation, purchase-suggestion generation, orders, production, backups, reports, and unrelated routes are out of scope.

## Next runtime slice

B3.2 — Alerts and Purchases feedback migration remains next. Do not assign a future pull request number before GitHub creates it.
