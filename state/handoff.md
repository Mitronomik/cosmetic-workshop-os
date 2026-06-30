# Handoff

## Last completed work

PR58 is complete: the frontend client card now includes `Пожелания клиента` and `Обратная связь` sections backed by the existing PR57 client-wish and feedback API. Wishes can be created, moved between active statuses, and explicitly archived; archived wishes are hidden by default and read-only when shown. Feedback can be created and viewed as append-only history with no edit/delete UI.

PR58 follow-up fixes preserve open wish and feedback form drafts during background client-card refreshes and when saving the main client details, including typed text, ClientRecipe selector values, dates, ratings, and follow-up checkbox state. Wish title maxlength is aligned with backend validation.

## Current repo state after PR58

Completed foundations include:

- Local-first project foundation with a backend API boundary and branded frontend shell.
- SQLite persistence, migration helpers, startup initialization, user data directory resolution, and backup-before-migration foundation.
- Onboarding state/API and first-run checklist UI.
- Ingredient/component backend and UI.
- Ingredient lot backend and UI.
- Immutable ingredient stock movements with derived balances and UI.
- Packaging item backend and UI.
- Immutable packaging stock movements with derived balances.
- Inventory read model and read-only inventory UI.
- Recipe templates, recipe versions, recipe ingredients, and read-only recipe calculation.
- Recipe UI for creating templates/versions and viewing backend calculation results.
- Catalog groups/tags backend plus browse-first/search/filter UX for components, packaging, recipes, clients, and client recipes where implemented.
- Clients backend and browse-first client UI.
- ClientRecipe backend and UI as a first-class individual formula entity copied from saved RecipeVersion composition.
- ClientRecipe composition update API and frontend composition editor that mutate only copied ClientRecipe rows, not source RecipeVersion rows.
- ClientRecipe restore workflow for archived ClientRecipes.
- Client wishes and append-only feedback backend.
- Client wishes and append-only feedback UI inside the client card, including draft-preservation fixes.

Backend exposes local API routes for health/settings/database status/onboarding, ingredients, ingredient lots, ingredient stock movements, packaging items, packaging stock movements, inventory reads, recipes/calculation, catalog categories/tags/assignments, clients, client recipes, ClientRecipe composition updates/restores, client wishes, and client feedback.

Orders, production readiness/confirmation, automatic stock write-off, production batches, alerts, purchase suggestions, import/export flows, backup/restore UI, cloud sync, mobile app/view, OCR, auth, and roles are not implemented and remain out of scope until explicitly requested.

## Important decisions

- Repo: `cosmetic-workshop-os`.
- Product: `Мастерская косметолога`.
- MVP remains local-first and API-first.
- User data must live outside the repository/code bundle.
- SQLite is the current persistence foundation.
- Stock changes are represented through immutable movements; balances are derived from movement history.
- Recipe history is protected through `RecipeTemplate -> RecipeVersion`.
- `ClientRecipe` is first-class and stores copied composition rows independent of source RecipeVersion rows.
- Client wish/feedback links to ClientRecipe are historical/context links and do not mutate formulas, inventory, orders, or production.
- Sensitive client notes/wishes/feedback must not be logged verbatim in debug output or audit summaries.

## Known testing limitations

- In this Codex environment, full FastAPI/Starlette `TestClient` test runs can be blocked if backend test dependencies are not installed. A prior attempt to install `backend[test]` was blocked by registry/proxy 403 while fetching build dependencies.
- Frontend onboarding fetches `/api/onboarding`; if the frontend is served separately without the backend proxy/runtime, it intentionally falls back to a non-technical unavailable state.

## Next recommended task

Orders backend foundation.

Keep the next PR narrow: add only the backend/domain/data-model/API foundation needed for orders. Do not add production readiness, production confirmation, automatic stock write-off, production batches, alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, or roles unless the task explicitly scopes them.

## Commands to rerun during handoff

- `git status --short`
- `git branch --show-current`
- Documentation-only state sync: `git diff -- README.md state/current-focus.md state/progress.md state/handoff.md docs/api.md`
- For implementation PRs after this handoff, rerun the relevant backend/frontend tests for the touched area.
