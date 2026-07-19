# Current focus — A3.7 Orders structured validation

A3.7 is implemented in the current focused runtime pull request. It is **not DONE** until the PR is reviewed, merged, and external exact-head browser smoke runs against the published head.

No browser smoke has been run for A3.7 yet.

## Runtime scope for this pull request

A3.7 is limited to the existing Order create/edit forms and their safe mutation lifecycle. Backend validation remains authoritative.

This runtime PR implements:

- visible backend validation issues map through explicit Order field allow-lists only;
- unknown, aggregate, hidden, malformed, or protected issue paths remain in the form summary;
- rejected submits preserve the user's draft values, focus, caret, and selection where applicable;
- duplicate submissions are guarded;
- stale responses from older Order contexts cannot overwrite newer state;
- mutation success remains separate from list-refresh failure;
- existing orders, order history, production history, stock movements, and production batches are not silently mutated.

## Explicit A3.7 non-goals

- No order schema changes.
- No migrations.
- No status workflow redesign.
- No Production Readiness changes.
- No Production Confirmation changes.
- No inventory or production write-off changes.
- No cost, tax, or margin implementation.
- No responsive-table redesign.
- No dependency or CI changes.
- No unrelated route changes.

## Expected tests and smoke planning

The A3.7 runtime PR should include focused frontend validation and mutation-lifecycle tests for Orders if the current tooling supports them, plus focused backend/API tests for backend-authoritative Order validation. Browser smoke should cover normal Order create/edit, structured backend `422` handling, draft/focus preservation, duplicate-submit protection, refresh-failure separation, stale-response protection, and no unintended mutation of existing order or production history.
