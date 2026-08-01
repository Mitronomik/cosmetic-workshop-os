# AuditLog workspace — durable product, API, privacy and presentation contract

Human-facing name: **Журнал действий**.

This document is the durable contract for the C3 AuditLog workspace. It is the authoritative source for the merged C3-I read boundary, the merged C3-II-A workshop-profile write boundary, the CR-009 file-backed artifact audit boundary, the actor field contract, the safe read model, the backend-owned display summary, ordering, pagination, filters, validation responses, privacy rules and the frontend presentation contract. The full CR-009 architecture decision is `docs/decisions/0013-file-backed-artifact-audit-semantics.md`. `docs/roadmap.md` PR27, `docs/implementation-plan.md` § C3, `docs/api.md`, `docs/domain-model.md` § 6.21 and `docs/architecture.md` § 6.18 defer to these durable contracts wherever they disagree.

---

## 1. Lifecycle status

```text
C3-I — Read-only AuditLog workspace
DONE — MERGED AND EXACT-HEAD VERIFIED
```

PR #159 `C3-I — Implement the read-only AuditLog workspace` is merged into `main`:

```text
Final reviewed and published head:
bf7cde060a43190fdf22c612a16b0c137aa5531b

Merge commit:
ba3ca7443e3280bc7f700af11e75dc4fa810665f

Merged at:
2026-07-30T03:20:23Z
```

Both commits are ancestors of the verified merged baseline. `GET /api/audit-logs` and `/settings/audit-log` now exist on merged `main`. This closes only the read-only slice; it does **not** complete the broader C3 write-side obligation.

Surrounding lifecycle:

```text
C1 — COMPLETED
C2 — COMPLETED
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-009 — ACCEPTED
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B2 — IMPLEMENTED ON PR BRANCH — NOT MERGED
C3-II-B3 — BLOCKED BY CR-004 — NOT AUTHORIZED
C3 — INCOMPLETE
C4 — INACTIVE — NEEDS PRODUCT DECISION
Product release readiness — NOT CLAIMED
```

`C3-II-A — Atomic workshop-profile AuditLog coverage` merged as PR #161 and is closed with honest exact-head attribution in § 16.7. `CR-009` accepts the durable file-backed partial-success and reconciliation contract. Its report-document slice `C3-II-B1` merged as PR #163 — final reviewed head `afd65fd2878fa02a0d4dc4963812c80644a4e787`, merge commit `ef0297e41a731f082a2a21a46b361aa9aac36cfa`, merged `2026-08-01T05:30:38Z`, final exact-head launcher smoke `PASS`, no unresolved P0 or P1 findings — so `report_document.created` exists on merged `main`. Export and backup coverage remain blocked by CR-006 and CR-004 respectively; the next authorized task is the evidence-only CR-006 diagnostic.

### 1.1. Implementation modules

| Layer | Module |
|---|---|
| Pure presenter | `backend/app/domain/audit_log_presentation.py` |
| Pure query validation | `backend/app/domain/audit_log_query.py` |
| Repository reads | `backend/app/repositories/audit.py` (`list_logs`, `distinct_filter_values`) |
| Service | `backend/app/services/audit_logs.py` |
| Response schemas | `backend/app/schemas/audit_logs.py` |
| Route | `backend/app/api/audit_logs.py` |
| Frontend DTO contract | `frontend/src/audit-log-contract.ts` |
| Frontend presentation | `frontend/src/audit-log-presentation.ts` |
| Frontend request lifecycle | `frontend/src/audit-log-workspace.ts` |
| Frontend DOM wiring | `frontend/src/audit-log-bindings.ts` |
| Route table | `frontend/src/app-navigation-routes.ts` |

In merged C3-I, `AuditLogRepository.create_log` was unchanged — the diff of that method was empty and no production write call site was touched. **No migration exists**; the only schema-adjacent change was the code-level enum member `DomainIssueCode.PAGINATION_OUT_OF_RANGE`.

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

## 3. The actor field — `actor_type`, not `source`

### 3.1. Decision

The persisted column, created by `backend/app/migrations/versions/0001_infrastructure.py` and written by `AuditLogRepository.create_log`, is:

```text
actor_type
```

The C3-I API field keeps that name:

```text
actor_type
actor_label
```

**`actor_type` is not renamed to `source`, and no `source` field is exposed or authorized in C3-I.**

### 3.2. Why a rename would have been wrong

The values the current write call sites actually produce are `system` and `user`. Those describe **who or what initiated the action** — the actor. They are not the process/source vocabulary that `docs/domain-model.md` § 6.21 and `docs/architecture.md` § 6.18 documented historically:

```text
manual
import
production
migration
backup
onboarding
restore
```

Mapping `actor_type` onto `source` would therefore not be a harmless read-time rename. It would silently change the meaning of the field, presenting an actor identity as if it were a process origin. C3-I does not do that.

### 3.3. A true process source is deferred

The `manual` / `import` / `production` / `migration` / `backup` / `onboarding` / `restore` vocabulary is **aspirational**. It cannot be implemented truthfully today, because no write call site persists a separate source/process dimension — there is no column, no parameter and no value carrying it.

A real `source` field would require write call sites to start persisting that dimension, which is a **write-side change** and is **not authorized here**. It needs a separately authorized product decision and implementation slice. Until then:

- no active document may call `system` or `user` a source;
- no active document may authorize the aspirational process-source vocabulary as implementable;
- C3-I exposes `actor_type` / `actor_label` only.

### 3.4. Persistence rules

- **Do not rename the database column.** `audit_logs.actor_type` keeps its name.
- **Do not migrate or backfill existing rows.** No database migration is authorized for `C3-I`.
- **Do not change existing AuditLog write call sites.** `AuditLogRepository.create_log(actor_type=...)` keeps its current signature and its `"system"` default.

### 3.5. Labels

```text
system → Система
user   → Пользователь
```

Any other persisted value — including values that may exist in an older local database — resolves to:

```text
unknown actor → Другой инициатор
```

The raw code may remain in the API item for forward compatibility, but the frontend must never display it as the primary user-facing label.

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
- `limit` and `offset` echo the effective applied values. Because invalid values are rejected rather than clamped (§ 7), these differ from the request only when a parameter was omitted and its default applied.
- `filter_options` carries the selectable filter values with their Russian labels (§ 7.5).

### 5.2. Item shape

Each item contains exactly:

```text
id
created_at
action
action_label
entity_type
entity_label
display_summary
actor_type
actor_label
```

Rules:

- `id` is an internal row identity and is **not displayed as a business value**. It exists for list keying and stable ordering only.
- `created_at` is returned as **ISO-8601 UTC** (`YYYY-MM-DDTHH:MM:SSZ`). The column is stored as SQLite `YYYY-MM-DD HH:MM:SS` UTC text via `CURRENT_TIMESTAMP`; the raw stored form is never exposed. Reuse the existing timestamp boundary in `backend/app/domain/tax_rate_timestamps.py` rather than adding a second converter.
- `action`, `entity_type` and `actor_type` are **stable codes**.
- `action_label`, `entity_label` and `actor_label` are **Russian user-facing labels**.
- `display_summary` is a **backend-owned safe Russian presentation value** built by the presenter in § 6. It is **never** the raw persisted summary.
- `entity_type` may be `null`, because the column is nullable. A `null` entity type carries the unknown-entity label (§ 5.4).

### 5.3. Never returned

- the raw persisted `audit_logs.summary` **verbatim**, its English technical prefix, or any use of it as an unrestricted API or frontend fallback. A suffix may contribute to `display_summary` only through the bounded allowlist rule of § 6.4;
- raw `metadata_json` — never returned in any form, whole or partial, parsed or stringified;
- `entity_id` — the persisted internal record identity is not part of the read model;
- internal entity IDs reached through any other route, including inside `display_summary` text;
- raw table names;
- stack traces, SQL, filesystem paths and raw payloads;
- sensitive client notes, allergies, addresses, wishes and feedback text — these must not be reconstructed or exposed, and the read must never join `clients`, `client_wishes`, `client_feedback` or any other business table to enrich a row;
- secrets of any kind;
- any `source` or `source_label` field (§ 3).

The read model is built from `audit_logs` alone.

### 5.4. Unknown codes must remain safe

```text
unknown action      → Другое действие
unknown entity type → Другая сущность
unknown actor       → Другой инициатор
```

The raw code may remain in the API item for forward compatibility, but the frontend must **never** display it as the primary user-facing label. A code added by a future write call site, or an unknown value already present in an older local database, therefore degrades to a safe Russian label instead of leaking a technical identifier or breaking the screen.

---

## 6. `display_summary` — the backend-owned presenter

### 6.1. Why the raw summary cannot be returned

The persisted `audit_logs.summary` values are write-time technical sentences. The inventory in § 11 shows what they actually look like: most are English, several embed internal record IDs (`Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`, `Recipe version created: template 3 v2`), and the `client_wish.*` summaries embed user-authored wish text.

Returning them verbatim would directly contradict the privacy and presentation rules of this contract: no internal IDs, no technical detail, no English technical text, no sensitive user-authored wish text, and no technical-admin presentation. So the raw summary is not returned at all.

### 6.2. The presenter

Define a focused backend module:

```text
AuditLogDisplayPresenter
```

or an equivalently focused module name consistent with the repository structure — for example `backend/app/domain/audit_log_presentation.py`, following the existing pure-domain pattern of `production_financials.py` and `report_financials.py`. It opens no connection, reads no repository, imports neither FastAPI nor Pydantic, and writes nothing.

### 6.3. Rules

- presentation is resolved from the known `action`;
- output is Russian and user-readable;
- **the raw persisted summary is never returned verbatim and is never used as an unrestricted API or frontend fallback**;
- internal IDs are never included;
- raw metadata is never included;
- no business-table join is performed;
- no historical row is rewritten — the persisted rows are untouched and stay append-only;
- sensitive wish text, client notes, allergies, addresses, feedback bodies and similar content are never included;
- a suffix extracted from the persisted summary may contribute to `display_summary` **only** under the bounded rule of § 6.4;
- `client_wish.*` must use a generic Russian summary and must **not** expose the persisted wish title;
- technical-ID summaries use generic Russian text without the ID;
- unknown actions, and recognized actions whose persisted summary does not match its expected shape, use a safe generic Russian `display_summary` — normally the resolved `action_label`;
- the frontend never receives the raw persisted summary.

### 6.4. Bounded suffix extraction — the exact allowlist

#### 6.4.1. The rule

```text
The raw persisted summary is never returned verbatim and is never used
as an unrestricted API or frontend fallback.

A suffix extracted from the persisted summary may contribute to
display_summary only when all of the following are true:

1. the action is explicitly allowlisted;
2. the persisted summary starts with the exact prefix assigned to that action;
3. the remaining suffix is non-empty;
4. the action is authorized to retain that category of business name;
5. the suffix is rendered only as plain text;
6. the suffix contains no internal identifier supplied by the presenter;
7. no database lookup or metadata lookup is performed.

Otherwise display_summary falls back to the generic action-specific phrase.
```

If any one of the seven conditions fails, the presenter uses the generic fallback. There is no partial credit and no repair attempt.

#### 6.4.2. Still prohibited

- returning the complete persisted summary;
- returning its English technical prefix;
- using it as an unrestricted fallback;
- returning summaries containing internal IDs;
- returning wish text;
- returning individual-recipe titles;
- returning metadata;
- joining business tables;
- rewriting historical rows.

#### 6.4.3. The exact prefix table

Inventoried from the merged-`main` production write call sites named in the last column. Every prefix below ends with a space after the colon; the retained suffix is everything after it. This table is exhaustive — an action absent from it can never retain a suffix.

| `action` | Exact persisted prefix | Retained suffix category | Generic fallback | `display_summary` template | Write call site |
|---|---|---|---|---|---|
| `client.created` | `Client created: ` | client full name | `Клиент создан` | `Клиент создан: <имя>` | `services/clients.py:18` |
| `client.updated` | `Client updated: ` | client full name | `Клиент изменён` | `Клиент изменён: <имя>` | `services/clients.py:30` |
| `client.deactivated` | `Client deactivated: ` | client full name | `Клиент архивирован` | `Клиент архивирован: <имя>` | `services/clients.py:36` |
| `ingredient.created` | `Ingredient created: ` | ingredient name | `Компонент создан` | `Компонент создан: <название>` | `services/ingredients.py:18` |
| `ingredient.updated` | `Ingredient updated: ` | ingredient name | `Компонент изменён` | `Компонент изменён: <название>` | `services/ingredients.py:37` |
| `ingredient.deactivated` | `Ingredient deactivated: ` | ingredient name | `Компонент архивирован` | `Компонент архивирован: <название>` | `services/ingredients.py:50` |
| `packaging_item.created` | `Packaging item created: ` | packaging item name | `Тара создана` | `Тара создана: <название>` | `services/packaging_items.py:18` |
| `packaging_item.updated` | `Packaging item updated: ` | packaging item name | `Тара изменена` | `Тара изменена: <название>` | `services/packaging_items.py:37` |
| `packaging_item.deactivated` | `Packaging item deactivated: ` | packaging item name | `Тара архивирована` | `Тара архивирована: <название>` | `services/packaging_items.py:50` |
| `recipe_template.created` | `Recipe template created: ` | recipe name | `Рецепт создан` | `Рецепт создан: <название>` | `services/recipes.py:25` |
| `recipe_template.deactivated` | `Recipe template deactivated: ` | recipe name | `Рецепт архивирован` | `Рецепт архивирован: <название>` | `services/recipes.py:37` |
| `order.created` | `Order created: ` | order product name | `Заказ создан` | `Заказ создан: <продукт>` | `services/orders.py:33` |
| `order.updated` | `Order updated: ` | order product name | `Заказ изменён` | `Заказ изменён: <продукт>` | `services/orders.py:53` |
| `order.cancelled` | `Order cancelled: ` | order product name | `Заказ отменён` | `Заказ отменён: <продукт>` | `services/orders.py:63` |
| `order.archived` | `Order archived: ` | order product name | `Заказ архивирован` | `Заказ архивирован: <продукт>` | `services/orders.py:72` |
| `catalog_category.created` | `Catalog category created: ` | reference-data name | `Категория справочника создана` | `Категория справочника создана: <название>` | `services/catalog.py:52` |
| `catalog_category.updated` | `Catalog category updated: ` | reference-data name | `Категория справочника изменена` | `Категория справочника изменена: <название>` | `services/catalog.py:76` |
| `catalog_category.archived` | `Catalog category archived: ` | reference-data name | `Категория справочника архивирована` | `Категория справочника архивирована: <название>` | `services/catalog.py:89` |
| `catalog_tag.created` | `Catalog tag created: ` | reference-data name | `Тег справочника создан` | `Тег справочника создан: <название>` | `services/catalog.py:102` |
| `catalog_tag.updated` | `Catalog tag updated: ` | reference-data name | `Тег справочника изменён` | `Тег справочника изменён: <название>` | `services/catalog.py:125` |
| `catalog_tag.archived` | `Catalog tag archived: ` | reference-data name | `Тег справочника архивирован` | `Тег справочника архивирован: <название>` | `services/catalog.py:138` |

Twenty-one actions, and no others.

#### 6.4.4. Explicitly excluded

- **`client_wish.*`** — the persisted suffix is a user-authored wish title. Never eligible.
- **`client_recipe.*`** — an individual-formula title can describe a client's personal condition, so it is treated as sensitive.
- **Any action whose persisted summary embeds an internal ID:** `ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created`, `production_confirmed`, `recipe_version.created`.
- **Any action without a stable exact prefix**, which includes every catalog-assignment action — `ingredient.catalog_category.assigned`, `ingredient.catalog_tags.updated`, `packaging_item.catalog_category.assigned`, `packaging_item.catalog_tags.updated`, `recipe_template.catalog_category.assigned`, `recipe_template.catalog_tags.updated`. Their persisted summaries are the fixed strings `Catalog category assigned` and `Catalog tags updated`, with no name to retain. Note that these actions share a dotted namespace with allowlisted groups; the allowlist is the exact 21-row table of § 6.4.3, **not** a prefix glob such as `ingredient.*`.
- Everything else in § 6.6.

Extending the allowlist requires a separate explicit decision in this document.

### 6.5. Required examples

These exact transformations are part of the contract:

```text
Ingredient lot created for ingredient #12
→ Создана партия компонента

Order #4 produced as batch #7
→ Производство заказа подтверждено

Client wish created: Убрать компонент X
→ Пожелание клиента добавлено
```

The first two show technical-ID summaries collapsing to generic Russian text with the ID dropped. The third shows `client_wish.*` discarding the user-authored wish title.

### 6.6. Full `display_summary` table

Where the table below shows a plain phrase, that phrase is the whole value. Where it shows `<…>`, the allowlist rule of § 6.4 applies and the generic phrase without the suffix is the fallback.

| `action` | `display_summary` |
|---|---|
| `catalog_category.created` | `Категория справочника создана: <название>` |
| `catalog_category.updated` | `Категория справочника изменена: <название>` |
| `catalog_category.archived` | `Категория справочника архивирована: <название>` |
| `catalog_tag.created` | `Тег справочника создан: <название>` |
| `catalog_tag.updated` | `Тег справочника изменён: <название>` |
| `catalog_tag.archived` | `Тег справочника архивирован: <название>` |
| `ingredient.catalog_category.assigned` | `Компоненту назначена категория` |
| `ingredient.catalog_tags.updated` | `У компонента изменены теги` |
| `packaging_item.catalog_category.assigned` | `Таре назначена категория` |
| `packaging_item.catalog_tags.updated` | `У тары изменены теги` |
| `recipe_template.catalog_category.assigned` | `Рецепту назначена категория` |
| `recipe_template.catalog_tags.updated` | `У рецепта изменены теги` |
| `client.created` | `Клиент создан: <имя>` |
| `client.updated` | `Клиент изменён: <имя>` |
| `client.deactivated` | `Клиент архивирован: <имя>` |
| `client_recipe.created` | `Создан индивидуальный рецепт` |
| `client_recipe.composition_updated` | `Изменён состав индивидуального рецепта` |
| `client_recipe.deactivated` | `Индивидуальный рецепт архивирован` |
| `client_recipe.restored` | `Индивидуальный рецепт восстановлен` |
| `client_wish.created` | `Пожелание клиента добавлено` |
| `client_wish.status_changed` | `Статус пожелания клиента изменён` |
| `client_wish.archived` | `Пожелание клиента архивировано` |
| `client_feedback.created` | `Добавлена обратная связь клиента` |
| `demo_data.installed` | `Установлены демонстрационные данные` |
| `demo_data.cleared` | `Демонстрационные данные удалены` |
| `import_draft_applied` | `Импорт применён` |
| `ingredient.created` | `Компонент создан: <название>` |
| `ingredient.updated` | `Компонент изменён: <название>` |
| `ingredient.deactivated` | `Компонент архивирован: <название>` |
| `ingredient_lot.created` | `Создана партия компонента` |
| `ingredient_lot.updated` | `Изменена партия компонента` |
| `ingredient_lot.deactivated` | `Партия компонента архивирована` |
| `onboarding.started` | `Начата первичная настройка` |
| `onboarding.step_completed` | `Выполнен шаг первичной настройки` |
| `onboarding.skipped` | `Первичная настройка отложена` |
| `onboarding.completed` | `Первичная настройка завершена` |
| `order.created` | `Заказ создан: <продукт>` |
| `order.updated` | `Заказ изменён: <продукт>` |
| `order.cancelled` | `Заказ отменён: <продукт>` |
| `order.archived` | `Заказ архивирован: <продукт>` |
| `packaging_item.created` | `Тара создана: <название>` |
| `packaging_item.updated` | `Тара изменена: <название>` |
| `packaging_item.deactivated` | `Тара архивирована: <название>` |
| `packaging_stock_movement.created` | `Добавлено движение тары` |
| `production_confirmed` | `Производство заказа подтверждено` |
| `recipe_template.created` | `Рецепт создан: <название>` |
| `recipe_template.deactivated` | `Рецепт архивирован: <название>` |
| `recipe_version.created` | `Создана версия рецепта` |
| `report_document.created` | `Документ отчёта создан` |
| `stock_movement.created` | `Добавлено движение сырья` |
| `tax_rate_setting_changed` | `Изменена налоговая ставка для расчётов` |
| `workshop_profile.updated` | `Профиль мастерской обновлён` |
| *(any unknown action)* | the resolved `action_label`, i.e. `Другое действие` |

`recipe_version.created`, `ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created` and `production_confirmed` are generic precisely because their persisted summaries embed internal IDs.

---

## 7. Ordering, pagination and filters

### 7.1. Ordering

Stable ordering:

```text
created_at DESC, id DESC
```

`created_at` has one-second precision, so ties are ordinary rather than exceptional; `id DESC` is what makes the order deterministic and makes pagination stable. The existing `idx_audit_logs_created_at` index already supports this ordering and no new index is required.

### 7.2. Pagination

Accepted values:

```text
limit default: 50
limit accepted range: integer 1..200
offset default: 0
offset accepted range: integer 0..9223372036854775807
```

#### 7.2.1. Validation order

The checks run in this exact order, and the **first** one that matches decides the code. This makes every invalid input map to exactly one code.

```text
1. Missing value
   limit  → default 50
   offset → default 0

2. Wrong type or representation
   non-integer
   fractional
   boolean
   malformed string
   → non_integer_quantity

3. Negative integer
   limit < 0
   offset < 0
   → negative_quantity

4. Non-negative value outside its accepted range
   limit == 0
   limit > 200
   offset > 9223372036854775807
   → pagination_out_of_range

5. Accepted values
   limit: integer 1..200
   offset: integer 0..9223372036854775807
```

Because step 3 precedes step 4, a negative `limit` is **only** `negative_quantity` and never `pagination_out_of_range`. Because step 4 is reached only by a non-negative integer, `limit == 0` and `limit > 200` are **only** `pagination_out_of_range`.

#### 7.2.2. Binding examples

```text
limit=true  → non_integer_quantity
limit=1.5   → non_integer_quantity
limit=abc   → non_integer_quantity
limit=-1    → negative_quantity
offset=-1   → negative_quantity
limit=0     → pagination_out_of_range
limit=201   → pagination_out_of_range
limit=200   → accepted
offset=0    → accepted
```

**An explicitly supplied invalid value is never silently clamped, coerced, rounded or ignored.** It is rejected with the structured `422` of § 8, never treated as a request for the nearest legal value.

Do not return an unbounded history. There is no "show everything" mode and no unlimited export path.

#### 7.2.3. The offset upper bound

```python
MAX_SQLITE_OFFSET = 9_223_372_036_854_775_807
```

The maximum signed 64-bit integer, which is the largest value SQLite can bind as `OFFSET`. A syntactically valid but larger offset would otherwise pass validation and then fail at bind time, so it is rejected as `pagination_out_of_range` — reusing the existing code, because no new `DomainIssueCode` member is authorized. This is a bounded robustness limit, **not** a schema change, **not** a migration, and **not** a new user capability.

`offset=9223372036854775807` is accepted; `offset=9223372036854775808` is `pagination_out_of_range`.

**Bounds are compared on the text, before conversion.** Validation verifies the exact decimal shape, strips leading zeroes, decides the sign, and compares digit length and lexicographic order against the field maximum; the value is converted to an integer only once it is known to fit. An arbitrarily long digit string is therefore classified as a range error rather than converted first — converting and only then range-checking is exactly what would turn a hostile query parameter into an unhandled error or an oversized bind. The rejected value is echoed back as a bounded excerpt, never as the whole supplied input.

Additional pinned edge semantics:

```text
limit=-0     → pagination_out_of_range   (zero, so the range check decides)
limit=0001   → accepted as 1
limit=000201 → pagination_out_of_range
offset=-0    → accepted as 0
offset=0000  → accepted as 0
limit  = 5000 positive digits → pagination_out_of_range
limit  = 5000 negative digits → negative_quantity
offset = 5000 positive digits → pagination_out_of_range
offset = 5000 negative digits → negative_quantity
```

None of these returns HTTP `500`, and no oversized offset ever reaches SQLite.

### 7.3. Authorized filters

```text
created_from
created_before
action
entity_type
actor_type
limit
offset
```

There is **no `source` filter** (§ 3). No other filter is authorized either — in particular no free-text search, no `entity_id` lookup and no metadata filter.

### 7.4. Filter rules

- `created_from` is **inclusive**;
- `created_before` is **exclusive**;
- both timestamps use **ISO-8601 UTC** (`YYYY-MM-DDTHH:MM:SSZ`) and are converted to the storage form for comparison;
- a malformed or otherwise invalid timestamp is rejected with a structured HTTP `422` carrying the existing `invalid_date` code, with `field` naming the offending parameter (`created_from` or `created_before`);
- `created_before <= created_from` is rejected with the structured HTTP `422` defined in § 8.2, rather than silently returning an empty result;
- empty filters return the latest events;
- filters combine with logical **AND**;
- filter options come from **values that actually exist in the current `audit_logs` table**, and are returned with safe Russian labels;
- filters perform **no writes**.

### 7.5. `filter_options`

`filter_options` reports the distinct `action`, `entity_type` and `actor_type` values that actually exist as rows in `audit_logs`, each paired with its Russian label resolved through § 11. It is derived from the current database contents, not from a hard-coded catalogue, so a fresh database yields short lists and no fabricated entries.

A value present in the database but absent from the known vocabulary — possible in an older local database — is returned with the corresponding unknown-code label from § 5.4. It is never dropped and never shown as a raw code.

#### 7.5.1. The exact nested DTO

This contract required filter options paired with Russian labels but did not define the nested keys. The implemented shape — the **one** implementation-level clarification `C3-I` adds — is:

```json
{
  "filter_options": {
    "actions": [
      { "value": "client.created", "label": "Клиент создан" }
    ],
    "entity_types": [
      { "value": "client", "label": "Клиент" }
    ],
    "actor_types": [
      { "value": "system", "label": "Система" }
    ]
  }
}
```

Rules:

- each option contains **exactly** `value` and `label`, and nothing else;
- values are the distinct values actually persisted in `audit_logs`; a fresh database therefore does **not** list all 52 known actions;
- options are derived from the whole current `audit_logs` table, not from the current filtered page, so they do **not** change merely because the result filters changed;
- labels come from the same backend resolver the list items use, so an unknown persisted code stays present under its safe fallback label;
- options are ordered deterministically by raw persisted value ascending;
- the raw code is never displayed as visible frontend text — it is the `<option value>` and the request parameter only;
- **`null` is omitted from `filter_options.entity_types`.** `null` is not an authorized query code and could not be selected without inventing a new filter sentinel, and no new query parameter or sentinel is authorized. Rows with `entity_type IS NULL` stay fully readable as items carrying `entity_label: "Другая сущность"` (§ 5.2, § 5.4).

#### 7.5.2. Blank query values

A blank or whitespace-only `action`, `entity_type`, `actor_type`, `created_from` or `created_before` is the "no filter selected" state of an empty `<option>` and is treated as **absent**, not as a request for rows whose code is the empty string — no persisted code is empty. This applies to filters only. A blank `limit` or `offset` is a malformed pagination value and is rejected under step 2 of § 7.2.1, never defaulted, because § 7.2.2 forbids reinterpreting an explicitly supplied invalid pagination value.

#### 7.5.3. Evaluation order across parameters

When one request carries several problems, the reported one is deterministic: the date parameters are validated first (`created_from`, then `created_before`, then the range conflict), then `limit`, then `offset`. Within `limit` and `offset` the ordered precedence of § 7.2.1 applies unchanged.

---

## 8. Validation wire contract

The existing router convention raises:

```python
HTTPException(
    status_code=422,
    detail=issue.__dict__,
)
```

so the `DomainIssue` object is the **value of `detail`**, not the whole response body. The exact HTTP body C3-I returns is:

```json
{
  "detail": {
    "code": "invalid_date",
    "message": "Russian user-readable message",
    "field": "created_from",
    "value": "the rejected value",
    "next_action": "Russian user-readable next action"
  }
}
```

Rules:

- do **not** describe a bare `DomainIssue` object as the complete wire response — the `detail` envelope is part of the contract;
- `message` and `next_action` are Russian and user-readable, per `AGENTS.md` § 7.3 and § 7.4;
- `field` names the rejected parameter (`created_from`, `created_before`, `limit`, `offset`), or the date range for a range conflict;
- `value` carries the rejected input as text, never a stack trace, SQL fragment or raw payload;
- raw Pydantic internals are never returned.

### 8.1. Codes

| Condition | `code` |
|---|---|
| malformed or invalid `created_from` / `created_before` | `invalid_date` |
| `created_before <= created_from` | `invalid_date` |
| non-integer, fractional, boolean or malformed `limit` / `offset` | `non_integer_quantity` |
| negative `limit` / `offset` | `negative_quantity` |
| non-negative `limit` outside `1..200` — that is, `0` or `> 200` | `pagination_out_of_range` |
| `offset` greater than `9223372036854775807` (`MAX_SQLITE_OFFSET`) | `pagination_out_of_range` |

The pagination rows follow the ordered precedence of § 7.2.1, so every invalid pagination input has exactly one code: `limit=-1` is `negative_quantity` only, and `limit=0` is `pagination_out_of_range` only.

`invalid_date`, `non_integer_quantity` and `negative_quantity` already exist in `DomainIssueCode` and are reused unchanged.

`pagination_out_of_range` is the **one** new `DomainIssueCode` member authorized by `C3-I`:

```text
PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"
```

It is authorized because no existing member carries out-of-range pagination semantics. It must **not** be replaced by `percentage_out_of_range`, `invalid_category`, `invalid_decimal` or `zero_quantity`, each of which would misstate the error to the user. This is an explicit bounded enum addition — not a schema change and not a migration. No other new code is authorized.

### 8.2. The date-range conflict response

For:

```text
created_before <= created_from
```

the exact structured error is:

```text
HTTP status: 422
code: invalid_date
field: created_before
value: the supplied created_before value
```

- the Russian `message` must explain that the end of the period must be later than its beginning;
- the Russian `next_action` must tell the user to select an end date later than the start date;
- **do not use an undefined synthetic field such as `date_range`.** `field` is always a real query parameter the user can act on, and for this conflict it is `created_before`.

An equivalent shape, with the Russian text owned by the implementation:

```json
{
  "detail": {
    "code": "invalid_date",
    "message": "Конец периода должен быть позже его начала.",
    "field": "created_before",
    "value": "2026-07-01T00:00:00Z",
    "next_action": "Выберите дату окончания позже даты начала."
  }
}
```

## 9. Read-only behavior

AuditLog reads:

- write **no** AuditLog record — opening or filtering the journal is never itself an audited event;
- mutate **no** business table;
- create **no** file;
- change **no** setting;
- trigger **no** regeneration of alerts, purchase suggestions, reports or documents;
- perform **no** cleanup or normalization of historical rows.

AuditLog remains **append-only**. Historical rows are never rewritten, repaired, re-summarized or deleted — the presenter of § 6 changes only what is *shown*, never what is *stored*.

---

## 10. Frontend

### 10.1. Route and title

Canonical route:

```text
/settings/audit-log
```

User-facing title:

```text
Журнал действий
```

Implementation note: the existing router in `frontend/src/main.ts` resolves `window.location.pathname` through a flat exact-match table and every current route is a single segment. `/settings/audit-log` is the first nested path, so route resolution, the navigation entry under `Данные и настройки`, and the dev-server/static fallback for a nested path all need to be handled by the slice. This is a routing detail, not a licence to restructure navigation.

### 10.2. The workspace must show

- date and time;
- action label;
- entity label;
- safe display summary;
- actor label;
- date range filter;
- action filter;
- entity filter;
- actor filter;
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

### 10.3. The screen must not show

- raw action codes;
- raw entity codes;
- raw actor codes;
- the raw persisted summary;
- raw JSON;
- `metadata_json`;
- database table names;
- internal entity IDs;
- stack traces;
- SQL;
- developer paths;
- GitHub or PR terminology.

### 10.4. Route lifecycle, draft filters and focus

#### 10.4.1. Automatic refresh on route re-entry

The runtime — not `main.ts` — owns what arriving at the route means. `enter()` decides by itself between three outcomes:

| Situation | Outcome |
|---|---|
| no accepted data yet | initial load, showing the loading state |
| accepted data already held | **automatic refresh** of the applied filters, rows staying visible |
| an equivalent request already in flight | no-op, so a duplicate entry never issues a second request |

Re-entry refresh exists because the journal is a history of what the user just did elsewhere: opening `Журнал действий`, creating an order, and returning must show the new event without pressing `Обновить`. The refresh keeps the currently accepted rows on screen, does not reset the controls, does not apply unconfirmed drafts, and replaces the list only after a valid successful response. A failed re-entry refresh retains the previous rows and shows the ordinary Russian refresh warning — never the initial-failure screen. Re-entry after an initial failure with no data starts a fresh initial load.

`leave()` detaches ownership from any request still in flight: the response may still arrive but can no longer settle anything, while rows, draft filters and applied filters are all preserved for the next visit. A callback from a previous visit can never settle the current one.

#### 10.4.2. Draft filters versus applied filters

Two separate values, with unambiguous meanings:

- **`draftFilters`** — what the controls currently show. Editing a control changes only this: no request, no change to the accepted rows, no change to `appliedFilters`, and **no full page render**.
- **`appliedFilters`** — the exact filters that produced the currently accepted list. They change only after a *successful* apply or clear.

The binding request matrix:

| Request kind | Filters used | Offset |
|---|---|---:|
| first initial load | draft filters | `0` |
| explicit apply filters | draft filters | `0` |
| clear filters | empty draft filters | `0` |
| manual refresh | applied filters | `0` |
| automatic re-entry refresh | applied filters | `0` |
| load more | applied filters | accepted item count |
| retry initial failure | draft filters | `0` |

So pressing `Обновить` after changing a control but before applying it refreshes what the user is actually looking at, rather than silently applying a filter they never confirmed.

On a successful apply the rows are replaced, `appliedFilters` becomes the exact request snapshot, the draft controls keep the same values, offset returns to `0`, and previous field and filter errors clear. On a failure the previous rows and the previous `appliedFilters` both survive, the user's drafts survive so they can correct and retry, and a later `Обновить` still refreshes the previously applied result.

#### 10.4.3. Dirty filter state

`filtersDirty` is a pure field-by-field comparison of `draftFilters` against `appliedFilters`. While the filters are dirty:

- `Обновить` refreshes the applied list and never applies the draft;
- `Показать ещё` is **disabled**, because appending rows produced by the old filters while different filters are visible would present one list as the answer to two questions;
- a short neutral Russian hint appears:

```text
Фильтры изменены. Нажмите «Применить фильтры».
```

The hint uses no technical vocabulary — the words "draft" and "applied" are contract terms, not user-facing text. After a successful apply or clear, `filtersDirty` is false again.

`Очистить фильтры` stays an explicit immediate action: it empties the controls and requests the unfiltered history at offset `0`. On success both sides are empty and the dirty state clears. On failure the controls stay empty, the previous rows and previous applied filters remain, the dirty state stays true, and the warning explains that previously applied conditions are still shown.

#### 10.4.4. Keyboard focus preservation

The application shell renders by replacing `root.innerHTML`, which destroys and recreates every control. Two rules keep that from costing a keyboard user their place:

- **A draft filter edit performs no render at all.** The native control already shows its new value, so only the pending hint, the load-more control and a stale error on the edited field are updated in place, through `frontend/src/audit-log-dom.ts`. Focus stays exactly where the user put it.
- **Renders that must happen are wrapped in a focus boundary.** Before the render the focused element is captured — but only when it is inside the AuditLog workspace, so a render never steals focus from elsewhere — identified by a stable `data-focus-key`, with the selection range for text-like inputs. After the render, focus returns to the equivalent element; if it no longer exists, focus lands on the workspace container rather than at an accidental document position. When the route itself is gone, no focus is moved at all.

Stable focus keys: `audit-log-workspace`, `audit-log-refresh`, `audit-log-filter-created-from`, `audit-log-filter-created-before`, `audit-log-filter-action`, `audit-log-filter-entity-type`, `audit-log-filter-actor-type`, `audit-log-apply-filters`, `audit-log-clear-filters`, `audit-log-load-more`, `audit-log-retry`. They are addressing only and are never shown to the user.

Visible `:focus-visible`, `aria-describedby` association, `aria-invalid` on an invalid date and `role="alert"` on the relevant error all remain.

#### 10.4.5. Local date validation and DST

The date controls collect a **local wall-clock** value, and the backend accepts only `YYYY-MM-DDTHH:MM:SSZ`. Converting carelessly is unsafe twice a year, and both failures are silent, so `frontend/src/audit-log-local-time.ts` rejects them instead:

| Local input | Outcome |
|---|---|
| blank | valid — means "no filter" |
| syntactically invalid or an impossible calendar date | rejected as `invalid` |
| a wall-clock time that does not exist (spring gap) | rejected as `nonexistent-local-time` |
| a wall-clock time that happens twice (autumn overlap) | rejected as `ambiguous-local-time` |
| otherwise | converted to the canonical UTC instant |

Detection verifies **all six** local components — year, month, day, hour, minute, second — after constructing the candidate date, because checking only the date is exactly what lets a spring gap through: the platform normalizes the *hour* while leaving the day intact. Ambiguity is found by counting, within a bounded window around the candidate, how many UTC instants map back to the same wall-clock components: zero means nonexistent, one means valid, more than one means ambiguous. The helper is pure, directly testable, and adds no date library and no dependency.

Under `Europe/Amsterdam` this is binding:

```text
2026-03-29T01:30 → accepted
2026-03-29T02:30 → rejected, nonexistent
2026-03-29T03:30 → accepted

2026-10-25T01:30 → accepted
2026-10-25T02:30 → rejected, ambiguous
2026-10-25T03:30 → accepted
```

When conversion fails: no network request starts, the error attaches to the exact date control, the accepted rows and previous `appliedFilters` are retained, the user's draft value is kept so it can be corrected, the Russian message is announced, and focus stays on or returns to the affected control. A non-blank date that cannot be converted is **never** silently omitted from the request — omitting it would quietly broaden the filter — and no value is ever silently shifted to a different instant. Backend canonical timestamp validation is unchanged and still protects direct API callers.

### 10.5. Module ownership

Use focused frontend modules, following the pattern already established by `settings-tax-*`, `report-financial-contract.ts` and `report-financial-presentation.ts`.

- Do **not** put C3 business, privacy, filter or presentation logic only in `frontend/src/main.ts`.
- The focused modules are `audit-log-contract.ts` (DTO and request planning), `audit-log-local-time.ts` (pure local→UTC conversion), `audit-log-workspace.ts` (route lifecycle and request ownership), `audit-log-presentation.ts` (Russian view model and markup), `audit-log-bindings.ts` (event routing), `audit-log-dom.ts` (targeted updates and the focus boundary) and `app-navigation-routes.ts` (route table).
- `frontend/src/main.ts` must **not grow net** because of this slice; extract route-specific logic instead. The correction head has `6380` lines, down from the `6398`-line merged baseline.
- No generic `utils`, `helpers`, `manager` or `common` dumping ground.
- The frontend renders `display_summary`, `action_label`, `entity_label` and `actor_label` as received. It performs no filtering of its own, no label fallback that reveals a raw code, and no reconstruction of any value the backend withheld.

---

## 11. Actual AuditLog inventory on merged main through PR #161

Inventoried from `backend/app/migrations/versions/0001_infrastructure.py`, `backend/app/repositories/audit.py` and every production `AuditLogRepository.create_log` call site.

**Scope of this inventory.** Merged PR #161 added exactly one production action, `workshop_profile.updated`. `C3-II-B1` (CR-009) then added exactly one more, `report_document.created`, plus its entity `report_document`, so the current action vocabulary contains 52 actions and the entity vocabulary 20; the suffix allowlist remains 21. These values were read from the code, **not** by querying a database that contains a row for every code. A real local database may hold fewer of them, and an older database may hold values no current call site produces. That is exactly why the unknown-code fallbacks of § 5.4 are mandatory and why `filter_options` (§ 7.5) is derived from rows that actually exist rather than from these tables. This inventory originated as the read-only C3-I inventory. C3-II-A added exactly one write call site for Workshop-profile changes, and C3-II-B1 added exactly one for report-document creation; no other AuditLog write call site changed. On merged `main` the write call sites for manual backup creation and JSON export creation remain absent. `C3-II-B2` adds exactly one more action, `export.created`, plus its entity `export_file`, on its unmerged PR branch — taking the branch vocabulary to 53 actions and 21 entities, with the suffix allowlist still 21 — and `C3-II-B3` stays blocked by CR-004.

### 11.1. `action` — 52 codes in the current write vocabulary

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
| `report_document.created` | Документ отчёта создан |
| `stock_movement.created` | Движение сырья добавлено |
| `tax_rate_setting_changed` | Налоговая ставка изменена |
| `workshop_profile.updated` | Профиль мастерской изменён |

Note the two naming shapes that already exist and are **not** normalized by `C3-I`: most codes are dotted (`client.created`), while `import_draft_applied` and `production_confirmed` are flat.

### 11.2. `entity_type` — 20 values in the current write vocabulary

| `entity_type` | Required `entity_label` |
|---|---|
| `app_setting` | Настройка приложения |
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
| `report_document` | Документ отчёта |
| `stock_movement` | Движение сырья |

`ImportDraft` is PascalCase while every other value is snake_case. This inconsistency is persisted history and is **matched as-is**. `C3-I` must not normalize, alias, or rewrite it.

The column is nullable; a `null` `entity_type` resolves to `Другая сущность`.

### 11.3. `actor_type` — 2 values in the current write vocabulary

| `actor_type` | Required `actor_label` |
|---|---|
| `system` | Система |
| `user` | Пользователь |

`system` is the `create_log` default. `user` is written by the tax-rate and Workshop-profile settings mutation services.

These are **actor identities, not process sources** (§ 3). Every value of the historical process vocabulary — `manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore` — is produced by **no** call site and is not implementable without a separately authorized write-side decision. Any other value found in a database resolves to `Другой инициатор`.

### 11.4. Metadata shapes found

`metadata_json` is a JSON object, `{}` when no metadata is supplied. The key sets produced by current call sites are:

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
| `report_document.created` | `operation_id`, `document_type`, `format`, `reconciled_after_failure` |
| `stock_movement.created` | `ingredient_id`, `ingredient_lot_id` |
| `tax_rate_setting_changed` | `setting_key`, `previous_configured`, `new_configured`, `previous_rate_percent`, `new_rate_percent`, `previous_effective_at`, `new_effective_at`, `source` |
| `workshop_profile.updated` | `setting_key`, `changed_fields`, `changed_field_count`, `previous_configured`, `new_configured` |

**No stored metadata contains free-text client notes, allergies, addresses, phone numbers, email addresses or feedback bodies.** It is dominated by internal foreign-key IDs, enum codes and counters. That is exactly the class of value a non-technical user must not be shown, which is why `metadata_json` is excluded from the read model in full rather than field-by-field.

`report_document.created` metadata is exactly four keys and nothing else. `operation_id` is the internal idempotency identity that makes exactly-once finalization provable; `reconciled_after_failure` is a plain boolean saying whether the event was written immediately or recovered later. No filename, path, request reason, Workshop-profile value, report content or entity count is stored, and `entity_id` — which holds the same opaque operation UUID — stays excluded from the read model like every other entity ID.

The `source` key inside `tax_rate_setting_changed` metadata is an unrelated internal write-time marker with the constant value `settings`. It is not an audit source dimension, it is never returned, and it must not be confused with the deferred process-source field of § 3.3.

### 11.5. Persisted summaries — why § 6 exists

Most persisted summaries are English technical sentences built at write time, for example `Client created: Анна Иванова`, `Order created: Дневной крем`, `Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`, `Recipe version created: template 3 v2`, and the value-free `Workshop profile updated` and `Report document created`. A minority are Russian: the four `onboarding.*` summaries, the two `demo_data.*` summaries and the three `tax_rate_setting_changed` summaries.

Classification:

| Class | Actions | `display_summary` treatment |
|---|---|---|
| Embeds an internal record ID | `ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created`, `production_confirmed`, `recipe_version.created` | generic Russian text, ID dropped |
| Embeds user-authored wish text | `client_wish.created`, `client_wish.status_changed`, `client_wish.archived` | generic Russian text, title never exposed |
| Embeds an individual-formula title | `client_recipe.*` | generic Russian text, title never exposed |
| Embeds an ordinary business name after a stable exact prefix | exactly the 21 actions enumerated in § 6.4.3 | the suffix may be retained under the bounded § 6.4.1 rule; anything else falls back to the generic phrase |
| Fixed string, no user value | `client_feedback.created`, `import_draft_applied`, `demo_data.*`, `onboarding.*`, `tax_rate_setting_changed`, `workshop_profile.updated`, catalog-assignment actions | generic Russian text |

Client **notes, allergies, addresses, preferences, special conditions and feedback bodies are never written into a summary** by any call site, so no such value can reach the workspace even before § 6 applies.

Because `display_summary` is derived from `action` and never from the raw stored text except through the narrow allowlist, the English wording, the internal IDs and the wish titles present in history are all invisible to the user without a single historical row being modified.

### 11.6. Coverage gap found

`AGENTS.md` § 3.5 and `docs/domain-model.md` § 3.8 both say that backup, export and settings changes are logged. On merged main, the tax-rate setting and Workshop profile are audited. The remaining write-coverage gap is limited to manual backup, JSON export and report-document generation.

`C3-I` did not add those write call sites. It is a completed read-only slice, and the gap is stated here so the workspace is not mistaken for complete coverage. The remaining gap is subdivided rather than assigned to one broad implementation PR:

```text
C3-II-A — Atomic workshop-profile AuditLog coverage
DONE — MERGED AND EXACT-HEAD VERIFIED

CR-009 — ACCEPTED
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B2 — IMPLEMENTED ON PR BRANCH — NOT MERGED
C3-II-B3 — BLOCKED BY CR-004 — NOT AUTHORIZED
```

`C3-II-A` covers the pure SQLite workshop-profile mutation and its AuditLog row on merged main. CR-009 decides the durable artifact-primary, partial-success and reconciliation semantics. Report-document runtime slice B1 merged as PR #163, so report-document creation is audited on merged main. `CR-006` is now accepted, so B2 is authorized after its decision PR merges but is **not implemented** — JSON export creation is still **not** audited on merged main. Manual backup remains blocked by `CR-004`.

---

## 12. C3-I non-goals

Not authorized:

- AuditLog edit;
- AuditLog delete;
- rollback or undo;
- restore from AuditLog;
- detail endpoint;
- metadata viewer;
- raw JSON viewer;
- returning the raw persisted summary through any field or fallback;
- a `source` field, a `source_label` field, or a source filter;
- persisting a new source/process dimension;
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

## 13. Architecture constraints

- local-first remains unchanged;
- user data remains outside the code and package;
- API-first backend remains required;
- AuditLog remains append-only;
- historical rows are never silently rewritten;
- privacy filtering is **backend-owned** — the backend decides what leaves the database, and the frontend cannot widen it;
- the frontend never receives raw metadata or the raw persisted summary;
- the screen remains understandable to a nontechnical workshop user;
- no technical admin panel;
- no migration;
- no hidden product or architecture decision;
- no unrelated documentation cleanup.

---

## 14. C3-I acceptance boundary

`C3-I` is complete only when: `GET /api/audit-logs` returns exactly the § 5.2 item shape, with `actor_type` / `actor_label` and no `source` field; `display_summary` is produced by the § 6 presenter, the persisted summary is never returned verbatim and never serves as an unrestricted fallback, and a suffix leaves the backend only through the seven conditions and the exact 21-row table of § 6.4; no internal ID, English technical prefix, wish title, individual-formula title, metadata value or table name appears in any response; every invalid pagination input maps to exactly one code under the ordered precedence of § 7.2.1, and the date-range conflict returns `field: created_before`; ordering, pagination and filters behave exactly as § 7 defines, with invalid pagination rejected rather than clamped; every structured rejection uses the exact `{"detail": {...}}` envelope of § 8; the `actor_type` column is neither renamed nor migrated and no write call site changes; `/settings/audit-log` renders every state in § 10.2 and none of the forbidden content in § 10.3; the C3 logic lives in focused modules and `frontend/src/main.ts` has not grown; the complete backend suite and every frontend test script are green; and an exact-head focused smoke against the published head confirms the read-only behavior of § 9 with isolated data.

PR #159 satisfied this runtime boundary with the accepted evidence in § 15. This lifecycle documentation records that closure; it does not substitute documentation-only work for runtime verification.

---

## 15. C3-I merged closure and accepted evidence

```text
C3-I — DONE — MERGED AND EXACT-HEAD VERIFIED
```

### 15.1. Exact PR #159 evidence

| Item | Verified value |
|---|---|
| PR | #159 — `C3-I — Implement the read-only AuditLog workspace` |
| State | `MERGED`, base `main` |
| Final reviewed and published head | `bf7cde060a43190fdf22c612a16b0c137aa5531b` |
| Merge commit | `ba3ca7443e3280bc7f700af11e75dc4fa810665f` |
| Merged at | `2026-07-30T03:20:23Z` |
| Exact-head focused frontend | `npm run test:audit-log-workspace` — `92 passed / 0 failed / 0 skipped` |
| Exact-head timezone-focused frontend | `TZ=Europe/Amsterdam npm run test:audit-log-workspace` — `92 passed / 0 failed / 0 skipped` |
| Exact-head all frontend `test:*` scripts | `PASS — 0 failed / 0 skipped` |
| Exact-head frontend build | `npm run build` — `PASS` |
| Exact-head `frontend/src/main.ts` | `6380` lines |
| Exact-head browser smoke | `PASS — EXACT-HEAD BROWSER SMOKE PASSED`, 60 scenarios |

### 15.2. Backend and API attribution — not transferred to the final head

The final UI correction changed no backend file. The latest complete and focused backend runs were executed on:

```text
2848880f2009158749398aec7d504c0364336ba9
```

Results:

```text
complete backend suite: 1364 passed / 0 failed
focused backend result: 422 passed
all established merged-baseline node IDs preserved: 942
```

The complete backend tree is byte-identical between:

```text
2848880f2009158749398aec7d504c0364336ba9
bf7cde060a43190fdf22c612a16b0c137aa5531b
```

The complete backend suite was **not re-executed** on `bf7cde060a43190fdf22c612a16b0c137aa5531b`.

The API smoke result:

```text
150 checks / 0 failures
```

was executed on `2848880f2009158749398aec7d504c0364336ba9`. The final head is backend-identical, but the API smoke was **not re-executed** after the final frontend-only correction. It is not an exact-final-head API smoke and must not be relabelled as `PASS — FULL AUTOMATED SMOKE PASSED`. The truthful final evidence is `PASS — EXACT-HEAD BROWSER SMOKE PASSED` plus the separately attributed backend and API results above.

### 15.3. Known limitations after closure

- The coverage gap of § 11.6 remains; closing C3-I does not complete C3.
- A true process `source` remains deferred; only `actor_type` exists.
- The detail endpoint remains superseded; there is no metadata or raw JSON viewer.
- Historical rows are shown, never repaired.
- Restore, packaging, installation verification, the update flow and full release-candidate smoke remain open.
- C4 remains `INACTIVE — NEEDS PRODUCT DECISION`; product release readiness is not claimed.

---

## 16. C3-II-A — Atomic workshop-profile AuditLog coverage

Status:

```text
DONE — MERGED AND EXACT-HEAD VERIFIED
```

This runtime slice merged as PR #161. The contract below is preserved as the boundary the merged implementation was held to.

### 16.1. User-visible purpose and event vocabulary

When a user makes a real semantic change to the workshop profile, the application records exactly one safe, human-readable event in `Журнал действий`. The journal explains only that the profile changed; it is not a settings diff viewer.

Authorized event:

```text
action: workshop_profile.updated
entity_type: app_setting
entity_id: workshop_profile
actor_type: user

action_label: Профиль мастерской изменён
entity_label: Настройка приложения
display_summary: Профиль мастерской обновлён

persisted technical summary: Workshop profile updated
```

No existing action code represents this event exactly. The slice adds this code to the existing backend-owned presenter vocabulary only. It introduces no `source`, `source_label`, process-source column, migration, second AuditLog table, generic event bus or generic settings mutation framework.

### 16.2. Atomic backend ownership

Validation and canonicalization happen before a transaction or write whenever possible. A real mutation follows exactly:

```text
validate and canonicalize request
→ open one transaction
→ read current workshop profile
→ determine whether a real semantic change exists
→ write the canonical workshop profile
→ write exactly one AuditLog row on the same connection
→ commit both together
```

The profile mutation and AuditLog insert share one caller-owned SQLite connection and transaction. A second independent database connection must not be opened while that mutation transaction is active.

Failure contract:

```text
AuditLog insert fails
→ profile update rolls back
→ no new AuditLog row exists
→ API returns failure
→ previous profile remains authoritative

profile persistence fails
→ no AuditLog row is committed
→ previous profile remains authoritative
```

Use the established `SettingsRepository(..., connection=...)`, `AuditLogRepository.create_log(..., connection=...)` and atomic tax-setting precedent. Do not add a new persistence architecture.

### 16.3. Canonical no-op

A canonically identical submission is a no-op:

- preserve the stored profile and its existing `updated_at`;
- perform no upsert;
- create no AuditLog row;
- return the current profile through the existing response shape;
- return the exact Russian message `Профиль мастерской уже сохранён без изменений.`.

Repeated identical submissions remain no-ops. `GET` remains read-only. Profile deletion and Clear semantics are not part of this slice. An empty-but-valid profile remains governed by the existing storage contract and must not become row deletion.

Empty-profile behavior is exact:

- missing row plus an empty request is a no-op and creates no row;
- an existing empty row plus an empty request is a no-op;
- a configured profile changed to all-empty is a real mutation: canonical empty JSON is persisted, the row is not deleted, and exactly one AuditLog row is created.

### 16.4. Audit privacy

The persisted summary, `display_summary` and metadata must never contain workshop name, master name, contact text, workshop note, address, phone number, email address, arbitrary profile text, raw JSON, old values, new values, or full request/response payloads.

Metadata contains exactly:

```text
setting_key
changed_fields
changed_field_count
previous_configured
new_configured
```

`setting_key` is `workshop_profile`; `changed_fields` is a sorted list drawn only from `workshop_name`, `master_name`, `workshop_contact_text`, and `workshop_note`; `changed_field_count` equals its length; the configured flags are booleans. No `source`, timestamp, raw JSON, old value or new value is stored.

The C3-I read API continues to expose only the backend-owned safe `display_summary`. It never exposes the raw persisted summary, metadata, profile values or internal setting payload.

### 16.5. Existing API, UI and history compatibility

- Preserve `GET` and `PUT /api/settings/workshop-profile`; add no endpoint.
- Preserve profile field names, response shape, validation limits, Unicode normalization and control-character rejection.
- Preserve Settings route ownership, the existing form lifecycle and mutation-versus-refresh behavior.
- Preserve report-document immutability and all historical documents byte-for-byte.
- No frontend production change is expected unless implementation evidence proves one narrowly scoped presentation change is required.
- The generic AuditLog workspace displays the new action through backend-owned labels and presentation; the frontend does not calculate or reconstruct it.
- Persistence failures return HTTP `500` with `detail.code = workshop_profile_not_saved`, message `Не удалось сохранить профиль мастерской. Предыдущие данные сохранены без изменений.` and next action `Повторите сохранение. Если ошибка повторяется, проверьте, что локальное приложение работает.` Existing validation `422`, database-not-initialized `409`, and the successful response model stay unchanged.

### 16.6. Runtime verification required by this PR

This C3-II-A runtime PR adds or extends backend coverage for all of the following:

1. a real profile change writes the setting and exactly one AuditLog row;
2. both writes use the same connection and transaction;
3. forced AuditLog failure rolls back the profile update;
4. forced profile persistence failure commits no AuditLog row;
5. validation failure writes neither profile nor AuditLog;
6. canonical no-op performs no upsert and writes no AuditLog;
7. no-op preserves `updated_at`;
8. repeated identical submissions remain no-ops;
9. `GET` creates no AuditLog row;
10. summary contains no profile value;
11. metadata contains no profile value;
12. contact text and workshop note never appear in persisted audit data;
13. the profile response shape is unchanged;
14. the AuditLog list exposes safe Russian labels and `display_summary`;
15. the read API exposes no raw summary, metadata, profile value or internal setting payload;
16. other settings rows remain unchanged;
17. existing report documents remain byte-identical;
18. existing atomic tax-setting audit behavior remains unchanged.

Run the directly affected focused backend suites and the complete backend suite. Preserve every existing node ID unless a rename is unavoidable and explicitly justified; do not delete, skip, `xfail` or weaken tests.

Frontend verification must run the focused Settings suites, `test:audit-log-workspace`, every existing frontend `test:*` script and `npm run build`. Add no frontend arithmetic, payload reconstruction or profile-value display.

The exact-head smoke must use an isolated database, user-data directory, `HOME`, browser profile and runner-owned dynamic ports. It must cover:

```text
open Settings
→ update workshop profile
→ verify successful response
→ open Журнал действий
→ see exactly one safe workshop-profile event
→ verify no profile value appears
→ repeat identical Save
→ verify no second AuditLog event
```

It must also inject AuditLog persistence failure and prove the profile remains unchanged, the API reports failure, no AuditLog row commits, the UI does not claim success, and a retry after removing the fault succeeds exactly once. Check desktop and narrow viewport, keyboard access, console errors, page errors, failed requests and duplicate mutation requests. This is focused exact-head smoke, not release smoke.

### 16.7. Merged closure and evidence attribution

PR #161 `C3-II-A — Implement atomic workshop-profile AuditLog coverage` is
`MERGED`, base `main`.

| Item | Verified value |
|---|---|
| Final reviewed and smoke-tested head | `6c327630d0e4cca3c566253bf9f8224aaaa33172` |
| Merge commit | `3fec160f08aa7e775aa3e7ea650e570bf48955ad` |
| Merged at | `2026-07-30T08:11:41Z` |
| Exact-final-head focused smoke | `PASS — EXACT-HEAD C3-II-A FOCUSED SMOKE PASSED` |

The focused backend result `591 passed / 0 failed / 0 skipped`, complete
backend result `1376 collected / 1376 passed / 0 failed / 0 skipped`, all
`1364` baseline node IDs preserved with `12` added, all `18` frontend `test:*`
scripts passing, focused AuditLog frontend `92 passed`, timezone-focused
AuditLog frontend `92 passed`, and frontend build `PASS` were executed on:

```text
354104cc326f1e1374324ef9128e5ef771a4a063
```

The final documentation-only head
`6c327630d0e4cca3c566253bf9f8224aaaa33172` was production/test byte-identical
to that tested head. The backend and frontend suites were **not rerun** on the
final documentation-only head and are not relabelled as exact-final-head runs.
The exact-head focused smoke is not release smoke.

---

## 17. CR-009 — Durable file-backed artifact AuditLog semantics

Status:

```text
ACCEPTED — NOT IMPLEMENTED
```

The authoritative decision is
`docs/decisions/0013-file-backed-artifact-audit-semantics.md`. This section
summarizes the binding C3 contract without replacing the ADR.

The boundary covers only user-initiated creation of:

- manual backup creation;
- JSON export creation;
- report-document generation.

Once one of these artifacts is fully written and verified, the artifact is the
authoritative primary result. A later AuditLog failure never deletes it, never
turns the whole result into a false `500` or `409`, never silently omits the
event, and never claims cross-resource atomicity.

Before file creation, one `prepared` operation must be committed to the bounded
`artifact_audit_operations` ledger. Preparation failure creates no file and
returns `artifact_audit_tracking_unavailable`. After artifact verification,
AuditLog insert and transition to `audited` commit in one SQLite transaction.
Failure leaves the artifact available, keeps the ledger `prepared` or
`pending_audit`, and returns HTTP `201` with:

```text
audit_status: pending
audit_message: <non-empty Russian warning>
```

Ordinary audited success returns `audit_status: recorded` and
`audit_message: null`. The primary `message` remains the artifact-result
message. The frontend shows artifact success plus a separate Journal warning,
does not show false failure, and does not send a duplicate create request.

For B1, preparation failure is exact HTTP `500` with code
`artifact_audit_tracking_unavailable`, message `Не удалось безопасно
подготовить создание документа. Документ не создан.` and next action `Повторите
создание документа. Если ошибка повторяется, перезапустите приложение.` No
document, metadata, AuditLog or prepared ledger row is committed; existing
request validation is unchanged.

The ledger identity is stable unique `operation_id`, an opaque
backend-generated canonical lowercase UUID; statuses are exactly `prepared`,
`pending_audit`, `audited`, and `abandoned`. B1 uses the exact conceptual
columns and constraints in ADR 0013 and creates only
`artifact_kind = report_document` /
`audit_action = report_document.created`. Safe filenames are validated on
write and reconciliation read. One active operation owns an exact
`(artifact_kind, primary_filename)` identity.

The two filename fields are internal safe relative reconciliation identities.
Report-document filenames contain no request reason. Future B2/B3 primary
filenames may include the canonical filename-derived reason segment accepted
by CR-005. The ledger has no separate reason column and stores no raw human
reason, request reason, export-manifest reason or other separate user-authored
text. CR-005 is not reopened; existing artifacts are not renamed or rewritten.
Ledger filenames are never copied into AuditLog or exposed through `GET
/api/audit-logs`.

Reconciliation runs only after successful initialization and migrations,
before the ordinary UI is served, and once before another create of the scoped
kind. It inspects only recorded safe filenames under the expected directory,
verifies the complete artifact unit, and uses the same idempotent finalizer.
GET/list/status endpoints do not reconcile. There is no background thread,
timer, cloud worker, unbounded retry, directory scan or filename-history
reconstruction. A per-operation finalization failure leaves the event
unresolved without making startup or the older artifact fail and without
hiding independent initialization or migration failures.

Exactly one AuditLog row is permitted per `operation_id`. The finalization
transaction uses one caller-owned, write-serialized SQLite connection. B1
compatibly extends `AuditLogRepository.create_log(...)` to return
`cursor.lastrowid`; parameters and optional caller connection remain intact and
existing callers may ignore the integer. Under `BEGIN IMMEDIATE` or an
explicitly tested architecture-equivalent lock, the finalizer returns the
existing ID for `audited`, inserts only for `prepared`/`pending_audit`, and
stores the inserted ID while marking the operation `audited`, or commits
neither. It adds no second insertion API, bypass or generic transaction
framework.

Report-document verification requires the complete twelve-point safe-name,
directory, regular-file, metadata parse/identity/type/format/extension/ID/size
and safe-path contract in ADR 0013 and `docs/report-documents.md`. It neither
rerenders content nor compares current report data. Missing failed creation
becomes `abandoned`; mismatched, malformed, unsafe or ambiguous state remains
unresolved, is not audited or deleted, and stays counted.

Reserved event vocabulary:

| Artifact | Action | Entity type | Persisted summary | Safe display summary |
|---|---|---|---|---|
| report document | `report_document.created` | `report_document` | `Report document created` | `Документ отчёта создан` |
| JSON export | `export.created` | `export_file` | `JSON export created` | `Экспорт создан` |
| manual backup | `backup.created` | `backup_file` | `Backup created` | `Резервная копия создана` |

Every event uses `entity_id = operation_id` and `actor_type = user`. Metadata is
restricted to the exact per-event keys in ADR 0013. Paths, filenames, reasons,
Workshop profile, artifact or database contents, entity counts, client
information, request/response payloads and arbitrary user text are prohibited.
`reconciled_after_failure` is boolean only. These actions are not added to the
suffix allowlist, and the C3-I read API remains the only Journal read surface.

Existing artifacts are not backfilled, renamed or rewritten. The automatic
`before_migration` startup backup stays outside CR-009, remains before
migrations, and must not depend on a ledger table that may not yet exist.

### 17.1. Runtime subdivision

```text
C3-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C3-II-B2 — IMPLEMENTED ON PR BRANCH — NOT MERGED
C3-II-B3 — BLOCKED BY CR-004 — NOT AUTHORIZED
```

C3-II-B1 merged as PR #163 (merge commit
`ef0297e41a731f082a2a21a46b361aa9aac36cfa`, final reviewed head
`afd65fd2878fa02a0d4dc4963812c80644a4e787`). It covers the next sequential ledger migration, bounded repository/domain
service, post-migration startup reconciliation, report-document pre-create
reconciliation, report-document integration, `report_document.created`,
additive create fields `audit_status` / `audit_message`, additive status field
`pending_audit_count`, frontend success-plus-warning presentation, tests and
focused exact-head smoke.

For B1, `pending_audit_count` counts exactly `report_document` operations in
`prepared` or `pending_audit`; it excludes `audited` and `abandoned`. The status
GET reads but never reconciles it, and the frontend presents it only as a
pending-Journal warning. The exact pending message says retry occurs at the
next startup or before the next document, never immediately or in the
background.

B1 tests must prove sequential, startup-plus-pre-create and concurrent
exactly-once behavior; one concurrent caller resolves the already-audited
result; AuditLog insert failure leaves the operation unresolved; and ledger
update failure rolls the insert back.

`CR-006` is **accepted** — the JSON export create-response fallback was
confirmed reachable in production-equivalent behavior, and the confirmation
contract is decided in
`docs/decisions/0014-json-export-create-confirmation-semantics.md`. `C3-II-B2`
therefore reuses the ledger, as **one bounded implementation pull request**. It
is **implemented on branch `claude/c3-ii-b2-json-export-audit` and not merged**,
so no `export.created` row exists on merged `main`.

On that branch JSON export creation reserves its exact final filename once,
commits one `prepared` `json_export` ledger row before writing the file, writes
to exactly that reserved path, verifies the exact artifact read-only, and
finalizes exactly one `export.created` row together with the `audited`
transition in one `BEGIN IMMEDIATE` transaction. No new migration is added;
`0020` is reused. Reconciliation runs at normal startup after migrations —
ordered after the report-document pass — and once before the next JSON-export
create. A finalization failure leaves the export in place and returns HTTP `201`
with `audit_status: pending`, never a false total failure and never a
compensating delete.

For B2, `pending_audit_count` on `GET /api/exports/status` counts exactly
`json_export` operations in `prepared` or `pending_audit`, excluding `audited`
and `abandoned`; that GET reads but never reconciles it. The `export.created`
event, its `entity_type = export_file`, its `entity_id = operation_id`, its
`actor_type = user`, its persisted summary `JSON export created`, its display
summary `Экспорт создан` and its exact allowed metadata keys — `operation_id`,
`export_schema_version`, `reconciled_after_failure` — are already fixed by
ADR 0013 § *Audit privacy and vocabulary* and are **unchanged** by `CR-006`. No
export filename, path, human reason, canonical reason, manifest, entity count,
exported data, database filename or path, request payload, response payload,
client data or arbitrary user text may reach AuditLog, and the action is not
added to the suffix allowlist. `C3-II-B2` scope, verification contract and
non-goals: `docs/implementation-plan.md` § *C3-II-B2 — JSON export AuditLog
coverage*.

`C3-II-B3` may reuse the ledger only after CR-004 resolves SQLite backup
consistency behavior; `CR-004` remains open and unchanged. C3 remains
incomplete; C4, Restore, packaging, installation, update and release-candidate
work remain inactive; product release readiness is not claimed.
