# Current focus — A3.8 Production Readiness persistent-write presentation correction

## Goal

Close the remaining human-review findings on Draft PR #123 by making the existing globally serialized production/cancel/archive ownership visible and accessible across Orders, while preserving the read-only Production Readiness boundary and existing request-generation architecture.

Reviewed history: PR #123 exists and remains Draft/IN REVIEW. Reviewed published head `b6413f9b38710c1d3b8e231a52206d9a9dd7b9be` closed the readiness freshness, same-Order reverse mutual-exclusion, behavioral presentation-test, escaping, and duplicate-request findings. Human review then found that unrelated Order persistent-write controls still looked enabled while the global owner guard rejected them, and that cancel/archive had no honest pending copy. The prior exact-head smoke bundle is unavailable, and keyboard traversal was not completed against that reviewed head, so A3.8 is not DONE.

## Allowed scope

- Existing Orders list/detail, Production Readiness presentation, and Production Confirmation guard only.
- Existing Order request-generation, context-invalidation, transient-owner, and per-order freshness architecture.
- One explicit global production/cancel/archive ownership helper; no concurrent persistent Order writes.
- Visible disabled/explanatory states for unrelated Order production, cancel, and archive controls.
- Honest `Отменяем…` / `Архивируем…`, native disabled, and ARIA busy states on the owning action.
- Stable readiness-region focus continuity from keyboard activation through loading and failure, without auto-focusing the retry action.
- Focused lifecycle and behavioral rendering tests, directly affected project state, and retained external exact-head smoke evidence.

## Non-goals

- No change to backend readiness calculations, FEFO, density conversion, inventory policy, cost, tax, margin, or eligibility rules.
- No change to Production Confirmation domain behavior, ingredient/packaging write-off, cancellation/archive backend rules, schemas, migrations, responsive tables, dependencies, CI, or unrelated routes.
- No generic global request manager, concurrent persistent Order writes, A3.9 work, or A4 work.

## Tests

- Run form-validation, targeted-validation-update, Order mutation lifecycle, Order readiness presentation, and build checks. Independent frontend scripts may run concurrently only because each uses a separate `dist-tests` output directory.
- Run focused backend Production Readiness and Orders suites plus full backend comparison with exact base `8c4a092d055fd221cb18da901cee9e90106b33a4`.
- Run `git diff --check`, status/diff review, and critical self-review.
- Publish the correction to the existing branch, then run full and keyboard browser smoke against the exact remote head with isolated data and exact readiness/production/cancel/archive request counts.
- Retain the final external smoke Markdown/JSON/log/database evidence bundle in an archive outside the repository. A missing bundle is `INCONCLUSIVE — RUNNER`.

## Acceptance criteria

- A valid production, cancel, or archive owner globally disables all other Order production/cancel/archive controls with visible Russian explanatory copy; it never gets overwritten by a second owner.
- Unrelated Order navigation and read-only inspection remain available; unrelated readiness remains available when its order-bound ownership is safe.
- Pending cancel/archive controls render the correct operation/order label, native disabled, `aria-busy="true"`, and danger styling; duplicate or synthetic dispatch starts one request.
- Controls recover after success/failure, and stale callbacks cannot clear a newer owner.
- Keyboard activation keeps focus in the readiness region across rerenders; Tab reaches the retry action naturally instead of restarting from `body`.
- Production Confirmation cannot open or submit while any persistent Order write owner is valid.
- The exact published-head smoke retains its evidence archive, proves keyboard traversal/focus with real Chrome/Chromium automation, and proves no unintended ProductionBatch, stock movement, or Order-status mutation from readiness.
- PR #123 stays Draft/IN REVIEW. A3.9 and A4 remain separate.
