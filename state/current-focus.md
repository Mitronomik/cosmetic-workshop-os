# Current Focus

PR64 is ready for review: backend production confirmation is implemented.

Implemented scope:

- `POST /api/orders/{order_id}/produce` with explicit `confirm=true` requirement.
- Transactional production batch persistence and ingredient/package stock write-off.
- Readiness re-check before writes.
- Lifecycle guards for cancelled, archived/inactive, delivered, already produced, and already batched orders.
- Historical snapshots for ingredient lots and packaging.
- API documentation and backend tests for production confirmation.

Next recommended task:

- Add the frontend production confirmation UI as a separate scoped PR, using the existing read-only readiness panel and the new backend confirmation endpoint.

Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, partial production, production undo/reversal, and lot override UI out of scope unless explicitly requested.
