# Current focus — B3.3 local artifacts and reports shared-feedback lifecycle

- PR: #136.
- Title: B3.3 — Local artifacts and reports shared-feedback lifecycle.
- Actual branch: `codex/b3.3-local-artifacts-and-reports-shared-feedback-lifecycle`.
- Base: `main`.
- Base SHA: `b11160cc1a06df24fa6666969154c37389e6ab65`.
- Published head before correction: `e0138cc9a05a7e5529bf9f0e16b2283eb080d55a`.
- State: open.
- Draft: false.
- Active correction: fix irreversible detached ownership, production-composed runtime tests, real focus recovery, warning/error separation, and reconciliation lock after ambiguous outcomes.
- Scope remains only `/backups`, `/exports`, `/report-documents`, `/reports`.
- No backend API, service, repository, schema, migration, report-generation, PDF-generation, backup, or export behavior changes are in scope.
- Required focused suite: `npm --prefix frontend run test:local-artifacts-reports-feedback` twice.
- Required regressions: dashboard/onboarding, help, alerts, purchases, form validation, targeted validation, order mutation lifecycle, order readiness presentation, and frontend build.
- Backend verification: focused backup/export/report/report-document suites and complete `pytest -q`; branch-only failure delta must remain zero against accepted baseline failures.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
