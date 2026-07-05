# Import format — CSV/XLSX drafts

PR77 implements the backend foundation for safe import drafts in **Мастерская косметолога**.

## Safety flow

All imports must go through this flow:

```text
upload → parse → draft → preview → validation → future confirmation → future apply
```

PR77 implements only upload, parsing, persistent drafts, preview rows, validation issues, listing, detail, and cancellation. There is no confirmation/apply endpoint yet, and import rows are not written to real business tables.

## Supported files

Supported in PR77:

- `.csv`
- `.xlsx`

Not supported in PR77:

- PDF;
- images (`.png`, `.jpg`, `.jpeg`, `.heic`);
- `.docx`;
- `.txt`;
- OCR or AI extraction.

## Limits

- Maximum file size: 5 MB.
- Maximum data rows: 5000.
- Maximum columns: 100.
- XLSX parsing reads the first visible worksheet only.

## CSV rules

- UTF-8 and UTF-8 BOM are supported.
- CP1251 fallback is supported for legacy Russian CSV files.
- Comma, semicolon, and tab delimiters are detected by safe sniffing.
- The first non-empty row is the header row.
- Headers and string values are trimmed.
- Empty files and files without headers are rejected.
- Duplicate headers are reported after normalization.
- Decimal semantics are not silently changed; decimal values must use a dot when validated as decimals.

## XLSX rules

- XLSX parsing is implemented in the backend without OCR.
- The first visible worksheet is parsed.
- Formula evaluation is not performed by the import service.
- Charts, images, and workbook styling are ignored.
- The first non-empty row is the header row.

## Header normalization

Headers are normalized for validation by trimming, lowercasing, and replacing whitespace with `_`.

Example:

```text
Full Name → full_name
```

Raw values are stored separately from normalized values so the user can review the original file content in the future UI.

## Supported target types

| Target type | Label | Required columns | Optional columns |
| --- | --- | --- | --- |
| `ingredients` | Компоненты | `name` | `inci_name`, `unit`, `density`, `notes` |
| `packaging_items` | Тара | `name` | `category`, `unit`, `cost`, `stock`, `minimum_stock` |
| `clients` | Клиенты | `full_name` | `phone`, `email`, `address`, `notes` |
| `recipe_templates` | Рецепты | `name` | `product_type`, `notes` |
| `ingredient_lots` | Партии компонентов | `ingredient_name`, `quantity`, `unit` | `ingredient_id`, `unit_cost`, `purchase_date`, `expiration_date`, `supplier`, `lot_number` |
| `orders` | Заказы | `client_name`, `product_name`, `target_batch_size_value`, `target_batch_size_unit` | `client_id`, `sale_price`, `due_date`, `notes` |

Missing required business columns create a draft with validation errors instead of failing the whole upload. This lets the user preview and fix the file later.


## Import aliases vs domain fields

Import draft column names are user-facing import aliases. They are not necessarily identical to internal domain/API field names. A later confirmation/apply PR must explicitly map import aliases to domain fields before writing to business tables.

## Validation issues

Validation issues are structured and visible through the API:

```json
{
  "severity": "error",
  "code": "missing_required_column",
  "message": "Не найден обязательный столбец: name",
  "row_number": null,
  "field": "name"
}
```

Supported severities:

- `info`
- `warning`
- `error`

Examples of issue codes:

- `empty_file`
- `unsupported_file_type`
- `file_too_large`
- `too_many_rows`
- `too_many_columns`
- `missing_header`
- `duplicate_header`
- `missing_required_column`
- `missing_required_value`
- `unknown_column`
- `invalid_decimal`
- `invalid_date`
- `invalid_unit`

## What PR77 does not do

PR77 does not:

- apply import rows;
- create ingredients, clients, recipes, lots, orders, stock movements, production records, alerts, purchase suggestions, backups, or exports;
- add frontend UI;
- add import confirmation;
- add restore;
- add OCR/PDF/image import;
- use cloud services.

## PR79 readiness and validation refinements

Import draft API responses now include `draft.apply_readiness`. This contract answers whether the draft is validation-ready for a future explicit apply endpoint; it does **not** mean apply exists today.

Readiness statuses:

- `ready` — draft has rows, no errors, and no warnings/info issues.
- `ready_with_warnings` — draft has rows and no errors, but has warnings/info the user should review.
- `blocked` — draft has zero rows or at least one validation error. Future apply must be all-or-nothing, so any row error blocks the whole draft.
- `cancelled` — draft was cancelled and working data was not changed.
- `failed` — parsing/checking failed and working data was not changed.

Validation now recognizes deterministic Russian/user-friendly header aliases for supported targets, for example `Название` → `name`, `ФИО` → `full_name`, `Компонент` → `ingredient_name`, `Дата_покупки` → `purchase_date`, and `Цена` → `sale_price` for orders or `cost` for packaging. Alias use is always visible through `header_alias_used` info issues.

Decimal values keep raw source values in `raw_values`. A safe comma decimal such as `100,5` is normalized to `100.5` in `normalized_values` and emits `decimal_comma_normalized`. Ambiguous thousand formats such as `1.000,5`, `1,000.5`, or values with space thousand separators are blocked with `ambiguous_decimal`.

Unit aliases are normalized visibly: `г`, `gram`, `grams` → `g`; `мл`, `milliliter`, `milliliters` → `ml`; `шт`, `piece`, `pieces` → `pcs`. Each alias normalization emits `unit_alias_normalized`; unknown units remain `invalid_unit` errors.

Dates should use ISO `YYYY-MM-DD`. Deterministic Russian `DD.MM.YYYY` dates are normalized to ISO with `date_format_normalized`; ambiguous slash dates are not accepted.

Additional issue codes include `invalid_positive_decimal`, `invalid_non_negative_decimal`, `invalid_email`, `invalid_id`, `header_alias_used`, `decimal_comma_normalized`, `ambiguous_decimal`, `unit_alias_normalized`, and `date_format_normalized`. Unknown columns remain warnings and produce `ready_with_warnings`, not `ready`.

## PR80 — Backend apply foundation

PR80 adds the backend-only apply step for import drafts. Data is still parsed and validated through drafts first; production tables are changed only by an explicit API call:

```http
POST /api/imports/drafts/{draft_id}/apply
```

Required request flags:

- `confirm_apply=true` — explicit confirmation that the user wants to apply the draft.
- `backup_acknowledged=true` — acknowledgement that a backup was created or is not required. The endpoint does not create backups automatically.
- `allow_warnings=true` — required only for drafts with readiness `ready_with_warnings`.

Supported apply targets in PR80:

- `ingredients` — creates new component catalog records.
- `clients` — creates new client records.
- `recipe_templates` — creates catalog-only recipe templates; recipe versions and composition rows are not imported yet.
- `packaging_items` — creates catalog-only packaging records when safe.

Unsupported apply targets in PR80:

- `ingredient_lots` — remains blocked because lots affect inventory and must create stock movements correctly.
- `orders` — remains blocked because orders require client/recipe matching and production readiness implications.

Safety rules:

- Apply is all-or-nothing inside one database transaction.
- If one row conflicts or fails, zero rows are inserted.
- Existing records are never silently updated.
- Duplicate names/emails/phones inside the draft or in existing tables block the whole apply.
- Packaging rows with non-empty `stock` are rejected because stock must go through movements.
- No stock movements, lots, orders, production records, alerts, purchase suggestions, backups, or exports are created by PR80 apply.
- The frontend apply button is not implemented yet; PR81 is expected to add the confirmation/apply UI.
