# Handoff

## Last completed work
Implemented PR23 client recipes backend foundation. Added first-class `ClientRecipe -> ClientRecipeIngredient` persistence, validation, repository/service/API layers, and tests. A client recipe is created from an active client and existing source recipe version, and its ingredient lines are snapshotted from source `recipe_ingredients` into independent `client_recipe_ingredients` rows. Existing client recipes do not silently change when base recipe metadata or later recipe versions change.

## Current repo state
Backend exposes client recipe endpoints: `POST /api/client-recipes`, `GET /api/client-recipes`, `GET /api/client-recipes/{client_recipe_id}`, `GET /api/clients/{client_id}/recipes`, and `POST /api/client-recipes/{client_recipe_id}/deactivate`. Deactivation is soft (`is_active=0`, status `archived`). Audit actions `client_recipe.created` and `client_recipe.deactivated` are written in the same transaction as business writes.

## Scope intentionally not added
No frontend client recipe UI, client wishes/feedback, orders, production batches/readiness/write-off, stock reservation, FEFO allocation, cost/tax/margin, imports, exports, backup behavior changes, cloud, mobile, OCR, auth, or roles were added.

## Notes for next task
Future PRs can build client recipe calculation/UI on top of persisted snapshot rows. Do not treat client recipes as notes on clients or live views over recipe versions.

## Commands to rerun during handoff
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests launcher/tests`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`
- `git diff --check`
