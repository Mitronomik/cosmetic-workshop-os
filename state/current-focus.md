# Current Focus

## Status

PR62 — Production readiness backend foundation is implemented and ready for review.

## Completed in PR62

- Added backend Production Readiness service and schemas for order checks.
- Added `POST /api/orders/{order_id}/check-production-readiness`.
- Checks exact order recipe source (`RecipeVersion` or copied `ClientRecipe` composition), ingredient lot availability, FEFO candidate lots, packaging balance, expired/soon-expiring lots, density/conversion warnings, and optional cost/tax/margin estimates.
- Preserved read-only production boundary: no stock movements, no packaging movements, no production batches, and no order lifecycle mutation.
- Updated API docs and backend tests for readiness behavior.

## Next recommended task

Next roadmap step: production confirmation foundation as a separate scoped PR.

The next PR may add `ProductionBatch` and explicit stock/packaging write-off only if requested. Keep alerts, purchase suggestions, frontend production UI, import/export, cloud, mobile, OCR, auth, and roles out of scope unless explicitly requested.
