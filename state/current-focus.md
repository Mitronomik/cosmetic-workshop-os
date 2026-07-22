# Current focus

## Active slice
- Existing PR: #135 — Add Purchases shared-feedback lifecycle (B3.2b).
- Existing published branch: `codex/add-purchases-shared-feedback-lifecycle`.
- Reviewed starting head: `0cf2992329b5586d898da09c5de4b9fb820da056`.
- Base: `4692bdfa4d5171fb270687cb385a37571a8e9e2d`.
- B3.2a Alerts: merged.
- B3.2b Purchases: active correction.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## Correction goal
Complete the PR #135 correction for centralized Purchases route ownership, result-owned completion messages, production-shared reference-data ownership, production-shared control binding, and real focused tests that replace the rejected eight-test suite.

## Allowed files
- `frontend/src/main.ts`
- `frontend/src/purchase-suggestions-feedback.ts`
- `frontend/src/purchase-suggestions-runtime.ts`
- `frontend/src/purchase-suggestions-route.ts`
- `frontend/src/purchase-suggestions-reference-data.ts`
- `frontend/src/purchase-suggestions-bindings.ts`
- `frontend/test/purchase-suggestions-feedback.test.mjs`
- `frontend/tsconfig.test.purchase-suggestions-feedback.json`
- `frontend/package.json`
- `docs/implementation-plan.md`
- `state/current-focus.md`
- `state/handoff.md`
- `state/progress.md`

## Non-goals
- No backend API/service/repository changes.
- No migrations, schemas, dependencies, lock files, supplier features, stock receipt automation, Alerts runtime changes, unrelated route changes, or per-PR browser smoke.

## Required tests
- Focused Purchases suite twice.
- Existing Alerts, Dashboard/Onboarding, validation, Orders, Help suites.
- Frontend build.
- Focused backend Purchases suite and complete backend suite with branch-only failure delta 0.
