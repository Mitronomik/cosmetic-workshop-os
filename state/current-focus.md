# Current Focus

Current task: PR10 - Stock movements foundation.

## Allowed scope
Backend-only ingredient stock movement foundation for active ingredient lots: `stock_movements` migration, immutable movement domain validation, repository/service/API basics, derived lot balance helper, negative-balance prevention, minimal audit event, backend tests, smoke notes, and state documentation updates.

## Do not touch
Frontend inventory UI, recipes, production, automatic write-off, FEFO allocation, packaging inventory, packaging stock movements, clients, orders, purchase suggestions, imports/exports, launcher runtime changes, Docker, cloud/mobile access, OCR, auth, or roles.

## Acceptance
Stock movements belong to existing active ingredient lots, use positive Decimal quantities with explicit `in`/`out` directions, reject invalid lots/units/directions/quantities/fractional pieces/floats/percent units, derive current lot quantity from movements, prevent outgoing movements from making balance negative, do not add `remaining_quantity` or stored balance columns, keep movements immutable, and update state files with checks and smoke results.
