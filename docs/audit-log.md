# AuditLog workspace — durable product, API, privacy and presentation contract

Human-facing name: **Журнал действий**.

This document is the durable contract for the C3 AuditLog workspace. It is the authoritative source for the C3-I product boundary, the persistence-versus-API naming mapping, the safe read model, ordering, pagination, filters, privacy rules and the frontend presentation contract. `docs/roadmap.md` PR27, `docs/implementation-plan.md` § C3, `docs/api.md`, `docs/domain-model.md` § 6.21 and `docs/architecture.md` § 6.18 defer to this file wherever they disagree.

---

## 1. Lifecycle status

```text
C3-I — Read-only AuditLog workspace
AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED
```

`C3-I` is the **only** authorized C3 runtime slice. No other C3 slice exists, is planned, or is authorized. Nothing in this document is implemented on `main`; there is no branch, no PR number, and no runtime code for it. Do not start `C3-I` from this unmerged documentation branch.

Surrounding lifecycle at the time this contract was accepted:

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

---

## 2. Product purpose

The user needs a plain-language history of important workshop actions so they can understand what happened without opening SQLite, JSON, logs, GitHub or a terminal.

The user-facing name is:

```text
Журнал действий
```

The primary user is a non-technical cosmetic maker. The screen answers one question — *what exactly happened in the system?* — from `AGENTS.md` § 17.

### This is not

- a technical admin console;
- a database table browser;
- a security information and event management system;
- analytics;
- rollback;
- an event editor;
- a debugging console.

---

## 3. Persistence compatibility — `actor_type` versus `source`

The current database column, created by `backend/app/migrations/versions/0001_infrastructure.py` and written by `AuditLogRepository.create_log`, is:

```text
actor_type
```

The durable domain and API name is:

```text
source
```

`C3-I` maps persisted `actor_type` to API `source`. The mapping is a read-time rename inside the read model and nothing more.

Binding rules:

- **Do not rename the database column.** `audit_logs.actor_type` keeps its name.
- **Do not migrate or backfill existing rows.** No database migration is authorized for `C3-I`.
- **Do not change existing AuditLog write call sites merely to rename this field.** `AuditLogRepository.create_log(actor_type=...)` keeps its current signature and its `"system"` default.
- The API never exposes the column name `actor_type`, and the frontend never receives it.

`docs/domain-model.md` § 6.21 and `docs/architecture.md` § 6.18 already document the durable field as `source`. That documented name is now reconciled with the persisted column through this mapping instead of through a schema change.

### Documented versus actual source values

`docs/domain-model.md` § 6.21 lists an aspirational source vocabulary — `manual`, `system`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore`. The **actual persisted set on merged `main` is only `system` and `user`** (see § 10). `C3-I` presents the values that actually exist and treats every other value through the unknown-code rule. Expanding the written vocabulary would require changing write call sites and is **not** authorized here.

---

## 4. API

### 4.1. Authorized endpoint

Exactly one new endpoint is authorized:

```text
GET /api/audit-logs
```

It is read-only, local, unauthenticated like the rest of the local-first API, and belongs under the existing `/api` namespace.

### 4.2. Superseded detail endpoint

The old strategic-roadmap proposal in `docs/roadmap.md` § PR27 for:

```text
GET /api/audit-logs/{id}
```

is **explicitly superseded for the MVP**.

Reason:

- the MVP user goal is satisfied by a filtered readable list;
- raw metadata and technical detail increase privacy and complexity risk;
- a detail endpoint is not needed to understand the important action;
- it may be reconsidered only through a separate future product decision.

### 4.3. No write surface

No create, update, delete, rollback or export endpoint is authorized. `POST`, `PUT`, `PATCH` and `DELETE` under `/api/audit-logs` are all out of scope.

---

## 5. Safe read model

### 5.1. List response

The list response contains exactly:

```text
items
total
limit
offset
filter_options
```

- `total` is the number of rows matching the current filters, before `limit` and `offset` are applied.
- `limit` and `offset` echo the effective applied values, after defaults and clamping.
- `filter_options` carries the selectable filter values with their Russian labels (§ 7.3).

### 5.2. Item shape

Each item contains only:

```text
id
created_at
action
action_label
entity_type
entity_label
summary
source
source_label
```

Rules:

- `id` is an internal row identity and is **not displayed as a business value**. It exists for list keying and stable ordering only.
- `created_at` is returned as **ISO-8601 UTC** (`YYYY-MM-DDTHH:MM:SSZ`). The column is stored as SQLite `YYYY-MM-DD HH:MM:SS` UTC text via `CURRENT_TIMESTAMP`; the raw stored form is never exposed. Reuse the existing timestamp boundary in `backend/app/domain/tax_rate_timestamps.py` rather than adding a second converter.
- `action`, `entity_type` and `source` are **stable codes**.
- `action_label`, `entity_label` and `source_label` are **Russian user-facing labels**.
- `summary` is the **persisted safe summary**, rendered as plain text.
- `entity_type` may be `null`, because the column is nullable. A `null` entity type carries the unknown-entity label (§ 5.4).

### 5.3. Never returned

- raw `metadata_json` — never returned in any form, whole or partial, parsed or stringified;
- `entity_id` — the persisted internal record identity is not part of the read model;
- raw table names;
- stack traces, SQL, filesystem paths and raw payloads;
- sensitive client notes, allergies, addresses, wishes and feedback text — these must not be reconstructed or exposed, and the read must never join `clients`, `client_wishes`, `client_feedback` or any other business table to enrich a row;
- secrets of any kind.

The read model is built from `audit_logs` alone.

### 5.4. Unknown codes must remain safe

```text
unknown action      → Другое действие
unknown entity type → Другая сущность
unknown source      → Другой источник
```

The raw code may remain in the API item for forward compatibility, but the frontend must **never** display it as the primary user-facing label. A code added by a future write call site therefore degrades to a safe Russian label instead of leaking a technical identifier or breaking the screen.

---

## 6. Ordering and pagination

Stable ordering:

```text
created_at DESC, id DESC
```

`created_at` has one-second precision, so ties are ordinary rather than exceptional; `id DESC` is what makes the order deterministic and makes pagination stable. The existing `idx_audit_logs_created_at` index already supports this ordering and no new index is required.

Pagination:

```text
limit default: 50
limit minimum: 1
limit maximum: 200
offset default: 0
offset minimum: 0
```

Do not return an unbounded history. There is no "show everything" mode and no unlimited export path.

---

## 7. Filters

### 7.1. Authorized parameters

```text
created_from
created_before
action
entity_type
source
limit
offset
```

No other filter is authorized — in particular no free-text search, no `entity_id` lookup and no metadata filter.

### 7.2. Rules

- `created_from` is **inclusive**;
- `created_before` is **exclusive**;
- both timestamps use **ISO-8601 UTC** (`YYYY-MM-DDTHH:MM:SSZ`) and are converted to the storage form for comparison;
- malformed timestamps return the **existing structured Russian validation response** — HTTP `422` with the existing `DomainIssue` shape (`code`, `message`, `field`, `value`, `next_action`) from `backend/app/domain/errors.py`, using the existing `invalid_date` code. Do not invent a parallel error contract;
- `created_before <= created_from` is **rejected** with the same structured response;
- empty filters return the latest events;
- filters combine with logical **AND**;
- filter options come from **actual persisted values** and are returned with safe Russian labels;
- filters perform **no writes**.

### 7.3. `filter_options`

`filter_options` reports the distinct `action`, `entity_type` and `source` values that actually exist in `audit_logs`, each paired with its Russian label resolved through § 10. A value with no known label is returned with the corresponding unknown-code label from § 5.4. The option list is derived from persisted data, not from a hard-coded catalogue, so a fresh database yields short lists and no fabricated entries.

---

## 8. Read-only behavior

AuditLog reads:

- write **no** AuditLog record — opening or filtering the journal is never itself an audited event;
- mutate **no** business table;
- create **no** file;
- change **no** setting;
- trigger **no** regeneration of alerts, purchase suggestions, reports or documents;
- perform **no** cleanup or normalization of historical rows.

AuditLog remains **append-only**. Historical rows are never rewritten, repaired, re-summarized or deleted.

---

## 9. Frontend

### 9.1. Route and title

Canonical route:

```text
/settings/audit-log
```

User-facing title:

```text
Журнал действий
```

Implementation note: the existing router in `frontend/src/main.ts` resolves `window.location.pathname` through a flat exact-match table and every current route is a single segment. `/settings/audit-log` is the first nested path, so route resolution, the navigation entry under `Данные и настройки`, and the dev-server/static fallback for a nested path all need to be handled by the slice. This is a routing detail, not a licence to restructure navigation.

### 9.2. The workspace must show

- date and time;
- action label;
- entity label;
- safe summary;
- source label;
- date range filter;
- action filter;
- entity filter;
- source filter;
- `Очистить фильтры` (Clear filters);
- `Обновить` (Refresh);
- bounded pagination or `Показать ещё`;
- loading state;
- empty state;
- filtered-empty state;
- refresh failure retaining the previously accepted list;
- initial-load failure;
- narrow viewport;
- keyboard accessibility.

### 9.3. The screen must not show

- raw action codes;
- raw entity codes;
- raw source codes;
- raw JSON;
- `metadata_json`;
- database table names;
- internal entity IDs;
- stack traces;
- SQL;
- developer paths;
- GitHub or PR terminology.

### 9.4. Module ownership

Use focused frontend modules, following the pattern already established by `settings-tax-*`, `report-financial-contract.ts` and `report-financial-presentation.ts`.

- Do **not** put C3 business, privacy, filter or presentation logic only in `frontend/src/main.ts`.
- `frontend/src/main.ts` must **not grow net** because of this slice; extract route-specific logic instead. The current line count is `6398`.
- No generic `utils`, `helpers`, `manager` or `common` dumping ground.
- The frontend performs no filtering, no label resolution fallback that reveals a raw code, and no reconstruction of any value the backend withheld.

---

## 10. Actual AuditLog inventory on merged `main`

Inventoried from `backend/app/migrations/versions/0001_infrastructure.py`, `backend/app/repositories/audit.py` and every production `AuditLogRepository.create_log` call site. This is the real persisted vocabulary, not a documentation aspiration. Read-only inventory: no call site was edited.

### 10.1. `action` — 50 distinct persisted codes

| `action` | Required `action_label` |
|---|---|
| `catalog_category.created` | Категория справочника создана |
| `catalog_category.updated` | Категория справочника изменена |
| `catalog_category.archived` | Категория справочника архивирована |
| `catalog_tag.created` | Тег справочника создан |
| `catalog_tag.updated` | Тег справочника изменён |
| `catalog_tag.archived` | Тег справочника архивирован |
| `ingredient.catalog_category.assigned` | Компоненту назначена категория |
| `ingredient.catalog_tags.updated` | У компонента изменены теги |
| `packaging_item.catalog_category.assigned` | Таре назначена категория |
| `packaging_item.catalog_tags.updated` | У тары изменены теги |
| `recipe_template.catalog_category.assigned` | Рецепту назначена категория |
| `recipe_template.catalog_tags.updated` | У рецепта изменены теги |
| `client.created` | Клиент создан |
| `client.updated` | Клиент изменён |
| `client.deactivated` | Клиент архивирован |
| `client_recipe.created` | Индивидуальный рецепт создан |
| `client_recipe.composition_updated` | Состав индивидуального рецепта изменён |
| `client_recipe.deactivated` | Индивидуальный рецепт архивирован |
| `client_recipe.restored` | Индивидуальный рецепт восстановлен |
| `client_wish.created` | Пожелание клиента добавлено |
| `client_wish.status_changed` | Статус пожелания изменён |
| `client_wish.archived` | Пожелание клиента архивировано |
| `client_feedback.created` | Добавлена обратная связь клиента |
| `demo_data.installed` | Демонстрационные данные установлены |
| `demo_data.cleared` | Демонстрационные данные удалены |
| `import_draft_applied` | Импорт применён |
| `ingredient.created` | Компонент создан |
| `ingredient.updated` | Компонент изменён |
| `ingredient.deactivated` | Компонент архивирован |
| `ingredient_lot.created` | Партия компонента создана |
| `ingredient_lot.updated` | Партия компонента изменена |
| `ingredient_lot.deactivated` | Партия компонента архивирована |
| `onboarding.started` | Первичная настройка начата |
| `onboarding.step_completed` | Шаг первичной настройки выполнен |
| `onboarding.skipped` | Первичная настройка отложена |
| `onboarding.completed` | Первичная настройка завершена |
| `order.created` | Заказ создан |
| `order.updated` | Заказ изменён |
| `order.cancelled` | Заказ отменён |
| `order.archived` | Заказ архивирован |
| `packaging_item.created` | Тара создана |
| `packaging_item.updated` | Тара изменена |
| `packaging_item.deactivated` | Тара архивирована |
| `packaging_stock_movement.created` | Движение тары добавлено |
| `production_confirmed` | Производство подтверждено |
| `recipe_template.created` | Рецепт создан |
| `recipe_template.deactivated` | Рецепт архивирован |
| `recipe_version.created` | Версия рецепта создана |
| `stock_movement.created` | Движение сырья добавлено |
| `tax_rate_setting_changed` | Налоговая ставка изменена |

Note the two naming shapes that already exist and are **not** normalized by `C3-I`: most codes are dotted (`client.created`), while `import_draft_applied` and `production_confirmed` are flat.

### 10.2. `entity_type` — 19 distinct persisted values

| `entity_type` | Required `entity_label` |
|---|---|
| `app_setting` | Настройка |
| `catalog_category` | Категория справочника |
| `catalog_tag` | Тег справочника |
| `client` | Клиент |
| `client_feedback` | Обратная связь клиента |
| `client_recipe` | Индивидуальный рецепт |
| `client_wish` | Пожелание клиента |
| `demo_data_session` | Демонстрационные данные |
| `ImportDraft` | Черновик импорта |
| `ingredient` | Компонент |
| `ingredient_lot` | Партия компонента |
| `onboarding` | Первичная настройка |
| `order` | Заказ |
| `packaging_item` | Тара |
| `packaging_stock_movement` | Движение тары |
| `production_batch` | Производственная партия |
| `recipe_template` | Рецепт |
| `recipe_version` | Версия рецепта |
| `stock_movement` | Движение сырья |

`ImportDraft` is PascalCase while every other value is snake_case. This inconsistency is persisted history and is **matched as-is**. `C3-I` must not normalize, alias, or rewrite it.

The column is nullable; a `null` `entity_type` resolves to `Другая сущность`.

### 10.3. `actor_type` → `source` — 2 distinct persisted values

| Persisted `actor_type` | API `source` | Required `source_label` |
|---|---|---|
| `system` | `system` | Система |
| `user` | `user` | Пользователь |

`system` is the `create_log` default and is written by every call site except one. `user` is written only by `TaxRateSettingsService._write_audit` for `tax_rate_setting_changed`. Every other documented source value (`manual`, `import`, `production`, `migration`, `backup`, `restore`) is **not persisted anywhere** on merged `main`.

### 10.4. Metadata shapes found

`metadata_json` is a JSON object, `{}` when no metadata is supplied. The persisted key sets are:

| Action | Metadata keys |
|---|---|
| `catalog_category.*`, `catalog_tag.*` | `scope` |
| `*.catalog_category.assigned` | `catalog_category_id` |
| `*.catalog_tags.updated` | `tag_ids` |
| `client.*` | *(none)* |
| `client_recipe.created` | `client_id`, `source_recipe_version_id` |
| `client_recipe.composition_updated` | `changed`, `line_count` |
| `client_recipe.deactivated` | `client_id` |
| `client_recipe.restored` | `client_id`, `restored_status` |
| `client_wish.created` | `client_id`, `client_recipe_id`, `category`, `priority` |
| `client_wish.status_changed` | `client_id`, `client_recipe_id`, `old_status`, `new_status` |
| `client_wish.archived` | `client_id`, `client_recipe_id`, `new_status` |
| `client_feedback.created` | `client_id`, `client_recipe_id`, `feedback_type`, `sentiment`, `follow_up_needed` |
| `demo_data.installed` | `created_counts` |
| `demo_data.cleared` | `deleted_counts` |
| `import_draft_applied` | `target_type`, `applied_row_count`, `created_count` |
| `ingredient.created`, `ingredient.updated` | `category` |
| `ingredient_lot.*` | `ingredient_id` |
| `onboarding.started` | `current_step` |
| `onboarding.step_completed` | `step`, `next_step` |
| `onboarding.skipped` | `completed_steps`, `current_step` |
| `order.*` | order metadata built by `OrdersService._metadata` |
| `packaging_item.created`, `packaging_item.updated` | `kind` |
| `packaging_stock_movement.created` | `packaging_item_id` |
| `production_confirmed` | `order_id`, `production_batch_id`, `status`, `ingredient_rows`, `packaging_rows` |
| `recipe_version.created` | `recipe_template_id`, `version_number` |
| `stock_movement.created` | `ingredient_id`, `ingredient_lot_id` |
| `tax_rate_setting_changed` | `setting_key`, `previous_configured`, `new_configured`, `previous_rate_percent`, `new_rate_percent`, `previous_effective_at`, `new_effective_at`, `source` |

**No stored metadata contains free-text client notes, allergies, addresses, phone numbers, email addresses or feedback bodies.** It is dominated by internal foreign-key IDs, enum codes and counters. That is exactly the class of value a non-technical user must not be shown, which is why `metadata_json` is excluded from the read model in full rather than field-by-field.

### 10.5. Summaries found — safe and potentially sensitive

Most persisted summaries are English technical sentences built at write time, for example `Client created: Анна Иванова`, `Order created: Дневной крем`, `Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`. A minority are Russian: the four `onboarding.*` summaries, the two `demo_data.*` summaries and the three `tax_rate_setting_changed` summaries.

Summaries carrying **no** user free text: all `catalog_*`, `ingredient_lot.*`, `packaging_stock_movement.created`, `stock_movement.created`, `client_feedback.created` (fixed string `Client feedback created`), `import_draft_applied`, `production_confirmed`, all `onboarding.*`, all `demo_data.*`, all `tax_rate_setting_changed`, and both catalog-assignment summaries.

Summaries embedding a **user-authored value**:

| Action | Embedded value |
|---|---|
| `client.created` / `client.updated` / `client.deactivated` | client full name |
| `client_recipe.*` | client-recipe title |
| `client_wish.created` / `client_wish.status_changed` / `client_wish.archived` | client-wish title |
| `order.*` | order product name |
| `ingredient.*`, `packaging_item.*`, `recipe_template.*` | catalogue item name |

Assessment against the privacy rules: client **notes, allergies, addresses, preferences, special conditions and feedback bodies are never written into a summary**, so the workspace cannot expose them. A client name and an order product name are the business identities the user needs in order to recognize the event, and showing them is the point of the screen.

**One flagged residual risk — client wish titles.** `client_wish.*` summaries embed the wish title, which is user-authored wish text. `C3-I` returns the persisted summary verbatim, never reconstructs it and never joins to `client_wishes` for the wish description, so nothing new is exposed and no history is rewritten. Narrowing what future `client_wish.*` writes put into a summary would be a **write-side change to existing call sites**, which is explicitly out of scope here (§ 11), and rewriting existing rows is forbidden by append-only. Recording it as a bounded follow-up product decision is the correct next step; it is **not** decided or authorized by this document.

### 10.6. Coverage gap found

`AGENTS.md` § 3.5 and `docs/domain-model.md` § 3.8 both say that backup, export and settings changes are logged. On merged `main`, **only** the tax-rate setting is audited: there is no `create_log` call in `backend/app/services/backup.py`, `backend/app/services/export.py`, the report-document services, or `WorkshopProfileSettingsService.update_profile`. `Журнал действий` will therefore not show backup, export, report-document or workshop-profile events.

`C3-I` **must not** add those write call sites. It is a read-only slice, and the gap is stated here so the workspace is not mistaken for complete coverage. Closing the gap requires a separately authorized write slice.

---

## 11. C3-I non-goals

Not authorized:

- AuditLog edit;
- AuditLog delete;
- rollback or undo;
- restore from AuditLog;
- detail endpoint;
- metadata viewer;
- raw JSON viewer;
- CSV/XLSX/PDF audit export;
- charts;
- analytics;
- search over sensitive text;
- roles or permissions;
- multi-user actors;
- remote audit shipping;
- cloud sync;
- retention policies;
- log compaction;
- schema migration;
- backfill;
- changes to existing write semantics;
- C4;
- Restore;
- packaging;
- update flow;
- release-candidate smoke.

---

## 12. Architecture constraints

- local-first remains unchanged;
- user data remains outside the code and package;
- API-first backend remains required;
- AuditLog remains append-only;
- historical rows are never silently rewritten;
- privacy filtering is **backend-owned** — the backend decides what leaves the database, and the frontend cannot widen it;
- the frontend never receives raw metadata;
- the screen remains understandable to a nontechnical workshop user;
- no technical admin panel;
- no migration;
- no hidden product or architecture decision;
- no unrelated documentation cleanup.

---

## 13. C3-I acceptance boundary

`C3-I` is complete only when: `GET /api/audit-logs` returns exactly the § 5 read model; ordering, pagination and filters behave exactly as § 6 and § 7 define; `metadata_json`, `entity_id`, table names and technical detail never appear in a response; the `actor_type` → `source` mapping is read-time only with no migration and no write-site change; `/settings/audit-log` renders every state in § 9.2 and none of the forbidden content in § 9.3; the C3 logic lives in focused modules and `frontend/src/main.ts` has not grown; the complete backend suite and every frontend test script are green; and an exact-head focused smoke against the published head confirms the read-only behavior of § 8 with isolated data.

Documentation-only work does not satisfy any part of this boundary.
