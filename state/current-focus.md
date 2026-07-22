# Current focus — B3.3 local artifacts and reports shared-feedback lifecycle

- Active slice: B3.3 — Local artifacts and reports shared-feedback lifecycle.
- Branch: `codex/b3.3-local-artifacts-reports-feedback`.
- Base branch: `main`.
- Base SHA used locally: `b11160cc1a06df24fa6666969154c37389e6ab65`.
- GitHub PR number: not verified in this runner; publication is inconclusive because no GitHub remote or `gh` CLI is configured.
- Current local head: see final response for the post-commit SHA; publication is inconclusive in this runner.
- Scope: `/backups`, `/exports`, `/report-documents`, `/reports`.
- Architecture boundaries: frontend lifecycle and presentation ownership only; no backend API, service, repository, schema, migration, report-generation, PDF-generation, backup, or export behavior changes.
- Required focused suite: `npm --prefix frontend run test:local-artifacts-reports-feedback` twice.
- Required regressions: dashboard/onboarding, help, alerts, purchases, form validation, targeted validation, order mutation lifecycle, order readiness presentation, and frontend build.
- Backend verification: focused backup/export/report/report-document suites and complete `pytest -q`; branch-only failure delta must remain zero against the accepted baseline failures.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
