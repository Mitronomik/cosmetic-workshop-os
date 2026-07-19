# Current focus — A3.8 Production Readiness feedback and lifecycle

## Goal

Make the existing read-only Production Readiness check understandable, predictable, accessible, and safe before irreversible Production Confirmation. Backend calculations remain authoritative.

## Allowed scope

- Existing Orders detail and Production Readiness UI.
- Existing Order request-generation, context-invalidation, transient-owner, and cache architecture.
- Russian contextual rendering for blocking issues, warnings, recipes/formulas, components, selected lots, packaging, order-level issues, status, and estimate limitations.
- Separate system-failure feedback for `404`, `409`, structured `422`, local connection failures, and unexpected failures.
- Honest `Проверяем…` busy state, duplicate readiness prevention, and narrow guards for conflicting actions on the checked order.
- Focused frontend lifecycle tests and backend readiness no-write regression tests.
- Directly affected documentation and state files.

## Non-goals

- No change to `POST /api/orders/{id}/produce` or Production Confirmation behavior.
- No production batch creation, stock movement, inventory consumption/reservation, or order status transition.
- No FEFO, recipe, density, stock, expiration, cost, tax, margin, or eligibility calculation in the frontend.
- No database model, migration, schema, workflow, responsive table, dependency, CI, retry/backoff, route, or framework change.
- No A3.9, A4, or unrelated roadmap work.

## Tests

- Frontend form-validation, targeted-validation-update, Order mutation lifecycle, and build checks.
- Focused backend Production Readiness and Orders suites.
- Full backend comparison against the clean `8c4a092d055fd221cb18da901cee9e90106b33a4` base when baseline failures remain.
- Exact published-head browser smoke with isolated SQLite, ports, profile, deterministic fixtures, request counting, mutation checks, console diagnostics, and backend traceback checks.
- Repository hygiene and diff review.

## Acceptance criteria

- Valid ready, warning, and blocked results remain distinct from request/system failures.
- Backend messages are escaped and associated with the correct visible context where possible; unknown issues remain visible as general feedback.
- Rapid repeated action produces exactly one readiness POST.
- Loading ownership is honest and always released on completion, failure, navigation, or invalidation.
- Delayed, stale, wrong-order, and older callbacks cannot alter a newer Order context or clear a newer request owner.
- Cached results survive safe order navigation, but stale, failed, blocked, absent, or wrong-order results cannot enable Production Confirmation.
- Readiness creates no production batch, ingredient or packaging stock movement, reservation, or order status mutation.
- A3.9 Production Confirmation and A4 remain separate.
