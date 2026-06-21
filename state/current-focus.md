# Current Focus

Current task: PR13 - Packaging stock movements foundation.

## Allowed scope
Backend-only packaging/tare stock movement foundation: `packaging_stock_movements` migration, pieces-only movement validation, repository/service/API basics, movement-derived packaging balance, negative-balance prevention, transactional audit event, backend tests, smoke notes, and state documentation updates.

## Do not touch
Frontend packaging UI, packaging lots, packaging purchase list, packaging reservations, recipes, production, clients, orders, purchase suggestions, imports/exports, launcher runtime changes, final app packaging/installers, Docker, cloud/mobile access, OCR, auth, or roles.

## Acceptance
Packaging stock movements can be created/read/listed, packaging item balance is derived from immutable movement rows, incoming movements increase balance, outgoing movements decrease balance, outgoing movements cannot make balance negative, movement creation and `packaging_stock_movement.created` audit event are transactional, quantities are positive integer pieces only, floats/fractional pieces/percent/ml/g/arbitrary units are rejected, and no `current_quantity`, `remaining_quantity`, packaging lots, production, purchase list, or frontend UI are added.
