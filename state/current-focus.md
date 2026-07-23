# Current focus — B3.3 local artifacts and reports shared-feedback lifecycle

- PR: #136.
- Title: B3.3 — Local artifacts and reports shared-feedback lifecycle.
- Actual branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`.
- Base: `main`.
- Base SHA: `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Published head before this correction: `1e8a9fa8f063346cab5cb28c24c6eacf38e526a1`.
- State: open.
- Draft: false.
- Active correction: fix B3.3 reconciliation retry ownership and validated created-result boundaries without broadening scope.
- Scope remains only `/backups`, `/exports`, `/report-documents`, `/reports`.
- No backend API, service, repository, schema, migration, report-generation, PDF-generation, backup, or export behavior changes are in scope.
- Required focused suite: `npm --prefix frontend run test:local-artifacts-reports-feedback` twice.
- Required regressions: dashboard/onboarding, help, alerts, purchases, form validation, targeted validation, order mutation lifecycle, order readiness presentation, and frontend build.
- Backend verification: focused backup/export/report/report-document suites and complete `pytest -q`; branch-only failure delta must remain zero against accepted baseline failures.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.


## Current correction addendum — DOM binding and reconciliation regressions

- Correction commit scope: fix B3.3 DOM binding selectors, duplicate focus-key attributes, detached reconciliation sequencing, production focus construction, reconciliation-disabled controls, request-owned announcements, result-owned feedback cleanup, Dashboard navigation cleanup, Reports read-only harness, and dead helper cleanup.
- GitHub PR body is intentionally not updated by this correction; product owner will update it manually.
- Required verification remains the focused B3.3 suite twice, listed frontend regressions, frontend build, focused backend artifact/report suites, complete backend suite with branch-only failure delta 0, and repository integrity checks.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## Current correction addendum — remaining reconciliation/result-boundary gaps

- PR: #136.
- Branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`.
- Base: `main`; base SHA: `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Published head before this correction: `1e8a9fa8f063346cab5cb28c24c6eacf38e526a1`.
- Scope: detached-mutation reconciliation ordering, one queued authoritative GET after provisional failure, focusable create targets, accepted-only Export entity counts, accepted-only Report Document reason clearing, restored focused regression evidence, and dead helper cleanup.
- GitHub PR body must remain untouched by this correction.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## Current correction addendum — reconciliation retry ownership

- PR: #136.
- Branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`.
- Base: `main`; base SHA: `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Published head before this correction: `1e8a9fa8f063346cab5cb28c24c6eacf38e526a1`.
- Corrected invariant: `reconciliationRequired` controls the mutation lock; automatic GET execution is allowed only by one unconsumed post-settlement queue.
- GitHub PR body must remain untouched by this correction.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
