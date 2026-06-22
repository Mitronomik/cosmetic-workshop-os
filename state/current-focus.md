# Current Focus

PR21 — Ingredient stock movement UI foundation is implemented.

This slice adds the frontend `Движения склада` screen for ingredient lot stock movements only. The UI selects an ingredient lot, reads the backend-derived lot balance, lists append-only movement history, and creates new movements through the existing stock movement API.

Out of scope remains unchanged: no movement editing/deleting, no manual current balance input, no stored balances, no packaging stock movement UI, no production, no purchase list, no alerts, no new backend tables, and no migrations.

## PR22 — Clients backend foundation
- Added backend-only client directory foundation: `clients` table, domain validation, repository/service/API layers, and transactional audit events.
- No client UI, client recipes, wishes/feedback, orders, production, import/export, cloud, mobile, OCR, auth, or roles were added.
- `Client` is now ready as the backend dependency for future client-specific recipes.
