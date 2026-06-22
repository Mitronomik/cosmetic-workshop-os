# Current focus

PR24 is implemented: backend-only user-managed catalog categories and tags for ingredients/components, packaging/tare, and recipe templates.

Existing system classifications remain intact and continue to mean what they meant before PR24:
- `IngredientCategory` remains the fixed ingredient/component system enum;
- `PackagingKind` remains the fixed packaging/tare system enum;
- `recipe_templates.product_type` remains the existing free-text recipe template field.

The new catalog category/tag layer is additional organization metadata. Frontend catalog UI is still a follow-up.

Scope intentionally excludes production, orders, FEFO, stock write-off, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, roles, and any technical admin panel.
