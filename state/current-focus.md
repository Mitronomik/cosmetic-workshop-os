# Current Focus — Slice A3.2 Inventory structured validation closure

PR #114 is merged. Slice A2 structured form validation for `/clients` and `/ingredients` is complete.

PR #115 / Slice A3.1 Ingredient Lots structured validation is merged into main at merge commit `8b3ea5f7ab2b880d901250d111f6f5dca369c4b4`.

Current focused implementation slice: Slice A3.2 — migrate the remaining existing inventory forms that are present in the frontend:

- `/stock-movements` manual ingredient-lot Stock Movement create form;
- `/packaging-items` Packaging Item create form;
- `/packaging-items` Packaging Item edit form.

Scope constraints for PR116:

- reuse the shared structured validation parser and targeted DOM updater from PR #114/#115;
- keep backend inventory rules authoritative;
- keep all stock quantity changes flowing through existing stock-movement APIs;
- do not add migrations, new inventory architecture, direct packaging stock edits, or historical Stock Movement edit/delete actions;
- record that the current frontend Stock Movement route supports ingredient-lot movements only, while packaging movement APIs exist separately and remain follow-up UI work.

Slice A3 status: IN PROGRESS.
Slice A3.2 status: implementation corrected in PR116; merge pending. Remaining correction closes packaging adjacent-action guards and Stock Movement stale detail-render races; browser smoke remains reviewer-required unless run separately.
Recipe and recipe-version structured validation remain a later separate slice.
