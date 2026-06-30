# Current Focus

## Status

PR63 — Production readiness UI is implemented and ready for review.

## Completed in PR63

- Added a read-only `Проверить изготовление` action in the Orders detail view for active orders.
- The frontend calls the existing PR62 endpoint: `POST /api/orders/{order_id}/check-production-readiness`.
- The Orders workspace displays readiness summary, blocking issues, warnings, ingredient needs, FEFO-selected lots, packaging availability, and optional cost/tax/margin estimates from the backend response.
- The UI clearly states that the check does not write off stock, reserve lots, create production batches, or change order status.
- Cancelled, archived, or inactive orders do not expose the readiness action and show a safe read-only message.

## Next recommended task

Next roadmap step: production confirmation backend foundation as a separate scoped PR.

The next PR may add `ProductionBatch` persistence, explicit user confirmation, transactional ingredient/packaging stock write-off, order lifecycle transition, and audit logging only if requested. Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, and roles out of scope unless explicitly requested.
