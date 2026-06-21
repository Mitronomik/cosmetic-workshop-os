# Import Format

Document: `docs/import-format.md`  
Project: `cosmetic-workshop-os`  
Human-facing name: `Мастерская косметолога`  
Status: draft contract for future PR21/PR22 import work

---

## 1. Purpose

This document defines the expected CSV/XLSX import contract for MVP import work.

Imports are not implemented yet. This file exists so future implementation PRs have a single place for file-format rules and do not put import behavior only in prompts.

Use together with:

- `AGENTS.md`
- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/domain-model.md`
- `docs/roadmap.md`
- `docs/pr-testing-and-smoke-rules.md`

---

## 2. Hard rules

- MVP import formats: CSV and Excel/XLSX.
- Never write parsed rows directly into production tables.
- Every import must create an `ImportSource` and `ImportDraft` first.
- User must preview, validate, map columns when needed, and explicitly confirm before apply.
- Import apply must be transactional.
- Import apply must create an `AuditLog` entry.
- OCR/PDF/image imports are future scope only and must also produce drafts requiring manual confirmation.

---

## 3. MVP importable entities

Future import implementation should support drafts for:

- clients;
- ingredients;
- ingredient lots;
- packaging items;
- stock balances or stock movements;
- recipe templates when source data is structured enough.

Unsupported or ambiguous rows must remain in draft/error state until the user fixes or excludes them.

---

## 4. General CSV/XLSX expectations

- First row should usually contain column headers.
- UTF-8 CSV is preferred.
- Semicolon and comma delimiters may be accepted if implementation supports auto-detection.
- Decimal numbers may use `.` or `,` if normalized safely.
- Dates should be accepted only in documented formats.
- Empty optional fields are allowed.
- Empty required fields must produce row-level validation errors.

Recommended date formats:

```text
YYYY-MM-DD
DD.MM.YYYY
```

---

## 5. Validation error format

Human-readable import errors must identify:

- row number;
- column name;
- problematic value;
- expected format;
- suggested fix.

Example:

```text
В строке 7 в поле “Остаток” указано “много”. Нужно число, например 30 или 30,5.
```

Do not show raw parser stack traces or database errors to the user.

---

## 6. Entity column drafts

These are draft column contracts. Future PR21/PR22 may refine them while preserving the safe import flow.

### 6.1. Clients

Required:

- `name`

Optional:

- `phone`
- `email`
- `address`
- `notes`
- `allergies`
- `preferences`
- `status`

Privacy rule: sensitive notes may be imported only if the user explicitly imports clients. Do not log full notes verbatim.

### 6.2. Ingredients

Required:

- `name`
- `base_unit`

Optional:

- `inci`
- `category`
- `technological_role`
- `density`
- `default_purchase_price`
- `minimum_stock_threshold`
- `expiration_alert_threshold_days`
- `supplier`
- `status`

Density must be numeric if provided.

### 6.3. Ingredient lots

Required:

- `ingredient_name`
- `purchased_quantity`
- `remaining_quantity`
- `unit`
- `purchase_date`

Optional:

- `unit_cost`
- `total_cost`
- `expiration_date`
- `supplier`
- `lot_number`
- `status`

Validation rules:

- quantities must be non-negative;
- `remaining_quantity` must not exceed `purchased_quantity`;
- referenced ingredient must be matched or created only through confirmed import behavior.

### 6.4. Packaging items

Required:

- `name`
- `unit`

Optional:

- `category`
- `volume_capacity`
- `cost`
- `stock`
- `minimum_stock`
- `status`

### 6.5. Stock balances / movements

Required:

- `item_type`
- `item_name`
- `quantity`
- `unit`
- `reason`

Optional:

- `lot_number`
- `movement_type`
- `source`
- `occurred_at`

Stock import must still result in explicit `StockMovement` records after confirmation.

### 6.6. Recipe templates

Required if imported:

- `template_name`

Optional:

- `status`
- `version_number`
- `ingredient_name`
- `phase`
- `percentage`
- `comment`

Recipe import should validate total percentage and show warnings for totals below or above 100%. It must not silently normalize percentages.

---

## 7. Follow-up for implementation PRs

When PR21/PR22 implement imports, update this document with:

- exact accepted headers;
- sample CSV snippets;
- duplicate matching rules;
- supported date/number normalization;
- entity-specific preview behavior;
- apply/rollback guarantees.
