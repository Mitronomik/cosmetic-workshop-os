# Current Focus

Current task: PR11 - Packaging foundation.

## Allowed scope
Backend-only packaging/tare directory foundation: `packaging_items` migration, packaging kind/unit/capacity/cost validation, repository/service/API basics, minimal audit events, backend tests, smoke notes, and state documentation updates.

## Do not touch
Frontend packaging UI, packaging stock movements, packaging balances, packaging lots, recipes, production, clients, orders, purchase suggestions, imports/exports, launcher runtime changes, final app packaging/installers, Docker, cloud/mobile access, OCR, auth, or roles.

## Acceptance
Packaging items can be created/read/listed/updated/deactivated, use stable MVP kind codes, use pieces as their only stock unit, support optional positive Decimal capacity in ml or g, support optional non-negative Decimal unit cost, reject floats/invalid units/percent units/invalid capacity/cost, do not add `remaining_quantity` or `current_quantity`, and do not create packaging stock movement/balance/future business tables.
