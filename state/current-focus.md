# Current Focus — Slice A3.1 Ingredient Lots structured validation

PR #114 is merged. Slice A2 structured form validation for `/clients` and `/ingredients` is complete.

Current focused implementation slice: Slice A3.1 — migrate only `/ingredient-lots` create/edit to the structured frontend validation contract.

Scope for this branch:

- `/ingredient-lots` create form structured validation;
- `/ingredient-lots` edit form structured validation;
- explicit Ingredient Lot field-label allow-list;
- inline field errors, form-level summary, focus/caret preservation, stale-response and duplicate-submit guards;
- truthful separation of mutation success from post-save list-refresh failure;
- focused frontend tests and browser smoke evidence.

Explicit non-goal: `/stock-movements` is not part of A3.1 and must remain unchanged.

Other A3 candidate forms remain pending and must be handled by separate focused sub-slices.

Slice A3.1 status: IN PROGRESS — implementation under review.
