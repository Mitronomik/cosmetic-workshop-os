# backend/AGENTS.md

Scope: everything under `backend/`.

Backend-wide rules:

- Keep business logic in domain services, not in API route handlers.
- Keep API routes thin: validate input, call services, return schemas/errors.
- Database schema changes require migrations and must preserve existing local user data.
- Use `Decimal` for recipe, density, weight, stock quantity and money calculations.
- Do not use `float` for critical calculations.
- Imports must use `ImportSource` / `ImportDraft`, validation, preview and explicit user confirmation before production tables are changed.
- Production must be explicit and transactional: readiness check, user confirmation, `ProductionBatch`, `StockMovement`, order status update and `AuditLog` must succeed or roll back together.
- Stock changes must go through `StockMovement`; do not silently mutate inventory balances.
- Important business actions must create `AuditLog` entries.
- Do not log full sensitive client notes, allergies, skin conditions or private preferences.
- Backend changes require tests for affected domain services, API behavior, validation, transactions and migrations where relevant.
