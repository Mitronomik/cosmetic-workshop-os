# Current Focus — Slice A3.4 Client Recipe structured validation

Current baseline: PR #117 / Slice A3.3 is merged at merge commit `cce60e73670171717d9bfd619cd79e1c0b960fe9`.

A3.3 is closed and browser-smoke verified for Recipe Template creation and immutable Recipe Version creation. Slice A3 remains in progress because Client Recipe, Client Wishes, Client Feedback, Orders, and Production Confirmation validation are separate focused candidates.

Current focused implementation slice: Slice A3.4 — Client Recipe create and composition structured validation on `/client-recipes`. Do not assign a future PR number until GitHub creates it.

Scope for A3.4:
- migrate Client Recipe create (`POST /api/client-recipes`) to the shared structured backend-validation contract;
- migrate Client Recipe composition update (`PUT /api/client-recipes/{client_recipe_id}/ingredients`) to shared structured indexed validation;
- keep `status`, aggregate composition issues, generic `id`/`position`, indexed hidden `id`, malformed paths, ownership conflicts, and unknown nested fields in the form summary unless an approved visible field exists;
- preserve draft values, focus, caret, selected client, helper Recipe Template, selected source Recipe Version, row order, and non-inline errors after rejected saves;
- clear indexed composition errors on remove/move, preserve them on add-at-end, and clear composition validation on reset;
- prevent duplicate create and composition update requests through separate mutation lifecycle locks;
- preserve create success when the required list refresh fails;
- treat successful composition `PUT` response as authoritative without adding an artificial follow-up refresh.

Client Wishes and Client Feedback remain pending separate work. Orders and Production Confirmation remain pending separate work.
