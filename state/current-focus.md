# Current Focus

PR65 is ready for review: frontend production confirmation UI is implemented in the Orders workspace.

Implemented scope:

- Orders detail now shows production confirmation only after backend readiness allows production.
- The `Изготовить` action opens an inline second-confirmation panel with optional production notes.
- Confirmation calls `POST /api/orders/{order_id}/produce` with `confirm=true` and displays the returned production batch summary.
- Orders are refreshed from the backend after successful production so the status becomes `produced` from the source of truth.
- Production actions are hidden for cancelled, archived/inactive, delivered, and already produced orders.

Next recommended task:

- Production history read UI and production batch detail page.

Keep alerts, purchase suggestions, import/export, backup/restore UI, cloud, mobile, OCR, auth, roles, partial production, production undo/reversal, and lot override UI out of scope unless explicitly requested.
