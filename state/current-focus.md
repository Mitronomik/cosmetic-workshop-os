# Current focus

## Active slice
- B3.2a Alerts: merged.
- B3.2b Purchases: active.
- Base: `4692bdfa4d5171fb270687cb385a37571a8e9e2d`.
- Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

## Goal
Implement a Purchases-only shared-feedback lifecycle for `/purchase-suggestions` covering request ownership, snapshot/filter truth, local search, mutation identity, detached settlement, authoritative DTO handling, and reconciliation.

## Allowed scope
- `frontend/src/main.ts`
- `frontend/src/purchase-suggestions-feedback.ts`
- `frontend/src/purchase-suggestions-runtime.ts`
- Focused Purchases lifecycle tests and frontend package test script.
- Current implementation/state documentation for the temporary Block B smoke sequencing decision.

## Non-goals
- No backend purchase business-rule changes.
- No migrations or schema changes.
- No supplier management, online ordering, invoices, payment tracking, forecasts, PDFs, or stock receipt automation.
- No Alerts runtime behavior changes.
- No generic app-wide request framework.

## Required tests
- Focused Purchases suite twice.
- Existing Alerts lifecycle suite.
- Dashboard/onboarding, validation, order, help regression suites.
- Frontend build.
- Focused backend purchase suite and complete backend suite comparison when feasible.

## Acceptance
The slice is acceptable only if Purchases feedback is understandable and safe, no browser-smoke pass is claimed, backend-owned purchase rules remain backend-owned, and Block B integration smoke remains scheduled after all B slices.
