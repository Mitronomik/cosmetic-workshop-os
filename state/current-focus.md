# Current Focus — Slice A3.3 Recipe structured validation

Current baseline: PR #116 / Slice A3.2 is merged at merge commit `79286f076292645b3e83dfedfccb366dee1777f6`.

A3.2 is closed and browser-smoke verified for the inventory forms it covered. Slice A3 remains in progress because recipe and recipe-version validation are still being completed in focused sub-slices.

Current focused implementation slice: Slice A3.3 — structured validation for Recipe Template creation and immutable Recipe Version creation on `/recipes`.

Scope for A3.3:
- migrate Recipe Template create to the shared structured-validation contract;
- migrate immutable Recipe Version create to the same contract;
- map only approved recipe field paths, including explicit indexed ingredient paths such as `ingredients.0.amount_value`;
- keep unknown nested paths in the form summary;
- preserve draft values, focus, caret, and DOM node identity after rejected submits;
- prevent duplicate template/version POSTs and guard conflicting recipe-page actions while a mutation or required refresh is active;
- distinguish save failure from post-save refresh failure.

Recipe Version edit/delete remains prohibited. Existing saved recipe versions must remain immutable; changes are made only by creating a new version through the existing backend API.
