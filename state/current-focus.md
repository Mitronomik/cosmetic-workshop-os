# Current Focus

Current task: PR9 - Ingredient lots foundation.

## Allowed scope
Backend-only ingredient lot/batch foundation: `ingredient_lots` migration, lot domain validation, repository/service/API CRUD-style basics, deactivation, minimal audit events, backend tests, smoke notes, and state documentation updates.

## Do not touch
Frontend inventory UI, stock movements, remaining balances, FEFO allocation, production write-off/readiness/confirmation, recipes, clients, orders, packaging inventory, purchases, imports/exports, launcher runtime changes, Docker, cloud/mobile access, OCR, auth, or roles.

## Acceptance
Ingredient lots belong to existing active ingredients, invalid ingredient/date/cost/unit/density inputs are rejected, missing density and missing costs are accepted, Decimal-backed density/costs are stored as text, no stock balance or movement behavior is added, forbidden future tables are absent, checks/smoke are reported, and state files are updated.
