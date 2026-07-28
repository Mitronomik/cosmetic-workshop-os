# cosmetic-workshop-os - Domain Model

Документ: `docs/domain-model.md`  
Проект: `cosmetic-workshop-os`  
Клиентское название: «Мастерская косметолога»  
Статус: доменный контракт для MVP  
Версия: 1.0 draft  

---

## 1. Назначение документа

Этот документ описывает доменную модель проекта `cosmetic-workshop-os`.

Документ нужен для:

- проектирования БД;
- реализации backend models;
- реализации API schemas;
- реализации domain services;
- написания миграций;
- написания тестов;
- защиты от неправильного упрощения модели;
- синхронизации Codex Web с продуктовой логикой проекта.

Этот документ не является финальной SQL-схемой.  
Он описывает **доменный контракт**, который затем должен быть реализован через модели, миграции, сервисы и тесты.

Использовать вместе с:

```text
AGENTS.md
docs/product-spec.md
docs/architecture.md
docs/roadmap.md
docs/domain-glossary.md
docs/ui-ux-contract.md
docs/pr-testing-and-smoke-rules.md
```

---

## 2. Главный принцип модели

Система не является простой таблицей рецептов.

Она описывает рабочий цикл косметической мастерской:

```text
Client
→ ClientWish / ClientFeedback
→ RecipeTemplate / RecipeVersion / ClientRecipe
→ Order
→ ProductionReadiness
→ ProductionBatch
→ StockMovement
→ Alerts
→ PurchaseSuggestion
→ Reports / Backup / Audit
```

Главное ядро:

```text
Клиент
+ индивидуальная формула
+ заказ
+ фактическое производство
+ складские списания
+ история
```

---

## 3. Архитектурные инварианты доменной модели

Эти правила нельзя нарушать.

### 3.1. Рецепт не является одной плоской сущностью

Нельзя делать только `Recipe`.

Нужно разделять:

```text
RecipeTemplate
RecipeVersion
ClientRecipe
```

Где:

- `RecipeTemplate` - базовый рецепт;
- `RecipeVersion` - конкретная версия базового рецепта;
- `ClientRecipe` - индивидуальная формула конкретного клиента.

---

### 3.2. Индивидуальный рецепт не должен менять базовый рецепт

Если клиенту нужна индивидуальная формула, система должна создать отдельный `ClientRecipe` или отдельную версию индивидуального рецепта.

Нельзя:

```text
изменить RecipeVersion и считать, что это индивидуальный рецепт клиента
```

---

### 3.3. Склад меняется только через StockMovement

Нельзя просто менять остатки напрямую.

Все изменения остатков должны быть отражены в:

```text
StockMovement
```

Это нужно для истории, аудита, отчетов, производства и восстановления логики.

---

### 3.4. Компоненты учитываются через партии

Нельзя хранить только общий остаток компонента.

Нужно:

```text
Ingredient
→ IngredientLot
→ StockMovement
```

Партии нужны для:

- срока годности;
- закупочной цены;
- FEFO-списания;
- себестоимости;
- истории.

---

### 3.5. Производство должно быть transactional

Подтверждение производства должно происходить одной транзакцией:

```text
Create ProductionBatch
→ Create ProductionBatchIngredient
→ Create ProductionBatchPackaging
→ Create StockMovement
→ Update remaining quantities
→ Update Order status
→ Write AuditLog
```

Если любая часть падает, вся операция должна откатиться.

---

### 3.6. Импорт только через черновики

Импорт не должен сразу писать в production tables.

Обязательный поток:

```text
ImportSource
→ ImportDraft
→ validation
→ preview
→ confirmation
→ apply
```

---

### 3.7. Исторические данные не пересчитываются задним числом

Если позже изменился рецепт, цена компонента, плотность, налоговая ставка или упаковка, старые заказы и производственные партии не должны молча изменяться.

`ProductionBatch` должен хранить snapshot.

---

### 3.8. Важные действия логируются

Создание, изменение, архивирование, импорт, производство, списание, backup и изменение настроек должны попадать в `AuditLog`.

---

## 4. Общие технические правила

### 4.1. Идентификаторы

Рекомендуется использовать UUID или integer primary keys.  
Выбор зависит от реализации, но API не должен заставлять пользователя видеть технические ID.

### 4.2. Временные поля

Большинство сущностей должны иметь:

```text
created_at
updated_at
```

Для архивируемых сущностей желательно:

```text
archived_at
status
```

### 4.3. Денежные и расчетные значения

Использовать `Decimal`, не `float`.

Критичные Decimal-поля:

```text
percent
grams
ml
density
unit_cost
total_cost
sale_price
tax
margin
margin_percent
quantity
```

### 4.4. Soft delete

Для бизнес-сущностей предпочтительно архивирование, а не физическое удаление.

Архивировать:

```text
Client
RecipeTemplate
RecipeVersion
ClientRecipe
Ingredient
IngredientLot
PackagingItem
Order
```

Физическое удаление допустимо только для черновиков, demo/test данных или сущностей, которые не участвуют в истории.

### 4.5. User-facing labels

В БД могут храниться технические enum, но frontend должен показывать русские labels.

### 4.6. Sensitive data

Клиентские заметки, аллергии, адреса и обратная связь могут быть чувствительными.

Нельзя:

- писать полные sensitive notes в AuditLog;
- выводить sensitive data в debug logs;
- использовать real client data в тестах.

---

## 5. Entity relationship overview

```text
Client
  ├── Orders
  ├── ClientRecipes
  ├── ClientWishes
  ├── ClientFeedback
  └── Attachments

RecipeTemplate
  └── RecipeVersions
        ├── RecipeIngredients
        ├── Orders
        └── ClientRecipes

ClientRecipe
  ├── ClientRecipeIngredients
  ├── Orders
  ├── ClientWishes
  └── ClientFeedback

Ingredient
  ├── IngredientLots
  ├── RecipeIngredients
  ├── ClientRecipeIngredients
  ├── StockMovements
  └── PurchaseSuggestions

IngredientLot
  ├── StockMovements
  └── ProductionBatchIngredients

PackagingItem
  ├── Orders
  ├── StockMovements
  ├── ProductionBatchPackaging
  └── PurchaseSuggestions

Order
  ├── ProductionBatch
  ├── ClientFeedback
  ├── ClientWishes
  └── AuditLog

ProductionBatch
  ├── ProductionBatchIngredients
  ├── ProductionBatchPackaging
  └── StockMovements
```

---

# 6. Core entities

---

## 6.1. Client

### Назначение

Клиент косметолога.

Карточка клиента должна стать рабочим центром: контакты, история заказов, индивидуальные рецепты, пожелания, обратная связь и заметки.

### Fields

```text
id
first_name
last_name
phone
email
address
notes
allergies
preferences
special_conditions
status
created_at
updated_at
archived_at
```

### Status values

```text
active
archived
```

### Relationships

```text
Client → Order[]
Client → ClientRecipe[]
Client → ClientWish[]
Client → ClientFeedback[]
Client → Attachment[]
```

### Business rules

- `first_name` is required.
- `phone` is recommended, but not always required if user does not know it.
- `notes`, `allergies`, `preferences`, `special_conditions` are sensitive.
- Sensitive fields must not be copied fully into AuditLog.
- Client should be archived, not hard-deleted, if it has orders, recipes, wishes or feedback.
- Client card must show related history.

### Audit

Log:

```text
client_created
client_updated
client_archived
```

Audit summary must not include full sensitive notes.

---

## 6.2. ClientWish

### Назначение

Пожелание клиента, которое может повлиять на будущие заказы и индивидуальные рецепты.

Примеры:

```text
Сделать крем менее жирным.
Убрать аромат.
Не использовать компонент X.
Добавить более легкую текстуру.
```

### Fields

```text
id
client_id
related_order_id
related_client_recipe_id
text
importance
status
notes
created_at
updated_at
resolved_at
archived_at
```

### Status values

```text
new
considered
applied
rejected
postponed
archived
```

### Importance values

```text
low
normal
high
critical
```

### Relationships

```text
ClientWish → Client
ClientWish → Order optional
ClientWish → ClientRecipe optional
```

### Business rules

- `client_id` is required.
- `text` is required.
- Wish can be linked to order or client recipe, but this is optional.
- If a wish is used to change a formula, status should become `applied`.
- Rejected wish should keep reason in `notes`.
- Wish text may contain sensitive client info; do not log full text by default.

### Audit

Log:

```text
client_wish_created
client_wish_updated
client_wish_status_changed
client_wish_archived
```

---

## 6.3. ClientFeedback

### Назначение

Обратная связь клиента после использования продукта.

### Fields

```text
id
client_id
order_id
client_recipe_id
reaction_notes
liked
disliked
what_to_change_next_time
created_at
updated_at
archived_at
```

### Relationships

```text
ClientFeedback → Client
ClientFeedback → Order optional
ClientFeedback → ClientRecipe optional
```

### Business rules

- `client_id` is required.
- Feedback can be linked to order and recipe.
- Feedback can create or inform ClientWish.
- Feedback can lead to a new ClientRecipe version/copy.
- Feedback content can be sensitive.

### Audit

Log:

```text
client_feedback_created
client_feedback_updated
client_feedback_archived
```

Do not log full `reaction_notes`.

---

## 6.4. RecipeTemplate

### Назначение

Базовый рецепт, не привязанный к одному клиенту.

Пример:

```text
Крем дневной базовый
Сыворотка увлажняющая
Бальзам для губ
```

### Fields

```text
id
name
category
description
purpose
technology_notes
status
created_at
updated_at
archived_at
```

### Status values

```text
draft
active
archived
```

### Relationships

```text
RecipeTemplate → RecipeVersion[]
RecipeTemplate → ClientRecipe[]
```

### Business rules

- `name` is required.
- RecipeTemplate is a container for versions.
- Significant formula changes should create new RecipeVersion.
- RecipeTemplate can be archived.
- Archiving RecipeTemplate should not delete RecipeVersions.
- Existing orders and production history must remain valid.

### Audit

Log:

```text
recipe_template_created
recipe_template_updated
recipe_template_archived
```

---

## 6.5. RecipeVersion

### Назначение

Конкретная версия базового рецепта.

### Fields

```text
id
recipe_template_id
version_number
status
change_reason
notes
created_at
updated_at
archived_at
```

### Status values

```text
draft
active
archived
superseded
```

### Relationships

```text
RecipeVersion → RecipeTemplate
RecipeVersion → RecipeIngredient[]
RecipeVersion → Order[]
RecipeVersion → ClientRecipe[]
```

### Business rules

- `recipe_template_id` is required.
- `version_number` must be unique within RecipeTemplate.
- Active production/order references must use specific RecipeVersion.
- Historical versions must not be silently mutated.
- Editing active historical version should be restricted or should create a new version depending on implementation policy.
- Archived/superseded versions remain readable.

### Audit

Log:

```text
recipe_version_created
recipe_version_updated
recipe_version_archived
recipe_version_superseded
```

---

## 6.6. RecipeIngredient

### Назначение

Строка состава базовой версии рецепта.

### Fields

```text
id
recipe_version_id
ingredient_id
phase
percent
input_unit
sort_order
notes
created_at
updated_at
```

### Relationships

```text
RecipeIngredient → RecipeVersion
RecipeIngredient → Ingredient
```

### Business rules

- `recipe_version_id` is required.
- `ingredient_id` is required.
- `percent` must be Decimal.
- `percent` cannot be negative.
- Total percent of recipe version should be validated.
- System must not silently normalize percentages to 100.
- Archived ingredient in recipe should produce warning.

### Audit

Log changes through RecipeVersion-level summary or row-level audit if needed.

---

## 6.7. ClientRecipe

### Назначение

Индивидуальный рецепт конкретного клиента.

Это самостоятельная формула, а не просто заметка.

### Fields

```text
id
client_id
source_recipe_template_id
source_recipe_version_id
name
individualization_reason
notes
status
created_at
updated_at
archived_at
```

### Status values

```text
draft
active
archived
superseded
```

### Relationships

```text
ClientRecipe → Client
ClientRecipe → RecipeTemplate optional
ClientRecipe → RecipeVersion optional
ClientRecipe → ClientRecipeIngredient[]
ClientRecipe → Order[]
ClientRecipe → ClientWish[]
ClientRecipe → ClientFeedback[]
```

### Business rules

- `client_id` is required.
- Can be created from RecipeVersion by copying ingredient rows.
- Changes to ClientRecipe must not mutate source RecipeVersion.
- ClientRecipe should be calculable by same calculation service as RecipeVersion.
- Individualization reason should be stored.
- Future improvement: versioning of ClientRecipe if needed.

### Audit

Log:

```text
client_recipe_created
client_recipe_updated
client_recipe_archived
client_recipe_created_from_recipe_version
```

---

## 6.8. ClientRecipeIngredient

### Назначение

Строка состава индивидуального рецепта клиента.

### Fields

```text
id
client_recipe_id
ingredient_id
phase
percent
input_unit
sort_order
notes
created_at
updated_at
```

### Relationships

```text
ClientRecipeIngredient → ClientRecipe
ClientRecipeIngredient → Ingredient
```

### Business rules

- Same calculation rules as RecipeIngredient.
- Percent must be Decimal.
- Must not alter source RecipeIngredient.
- Archived ingredient should produce warning.

---

## 6.9. Ingredient

### Назначение

Компонент, используемый в рецептах.

Примеры:

```text
Масло ши
Вода
Эмульгатор
Консервант
Актив
Эфирное масло
```

### Fields

```text
id
name
inci
category
role
base_unit
density
default_unit_cost
minimum_stock
expiration_alert_days
supplier
notes
status
created_at
updated_at
archived_at
```

### Status values

```text
active
archived
```

### Unit values

```text
g
ml
pcs
```

### Relationships

```text
Ingredient → IngredientLot[]
Ingredient → RecipeIngredient[]
Ingredient → ClientRecipeIngredient[]
Ingredient → StockMovement[]
Ingredient → PurchaseSuggestion[]
```

### Business rules

- `name` is required.
- `density` is required only when ml to grams conversion is needed.
- If density is missing and ml conversion is requested, return warning.
- Ingredient can be archived, not hard-deleted, if used.
- `minimum_stock` is used for alerts and purchase suggestions.
- `expiration_alert_days` can override global setting.

### Audit

Log:

```text
ingredient_created
ingredient_updated
ingredient_archived
```

---

## 6.10. IngredientLot

### Назначение

Партия компонента с конкретным количеством, ценой и сроком годности.

### Fields

```text
id
ingredient_id
purchase_date
initial_quantity
remaining_quantity
unit
unit_cost
total_cost
expiration_date
supplier
lot_number
status
notes
created_at
updated_at
archived_at
```

### Status values

```text
active
depleted
expired
archived
```

### Relationships

```text
IngredientLot → Ingredient
IngredientLot → StockMovement[]
IngredientLot → ProductionBatchIngredient[]
```

### Business rules

- `ingredient_id` is required.
- `initial_quantity` must be positive.
- `remaining_quantity` cannot be negative.
- `remaining_quantity` cannot exceed `initial_quantity`.
- `unit_cost` should be Decimal.
- Expired lot should generate alert.
- Lot with zero remaining can become `depleted`.
- FEFO selection uses expiration_date.

### Audit

Log:

```text
ingredient_lot_created
ingredient_lot_updated
ingredient_lot_archived
ingredient_lot_depleted
```

---

## 6.11. PackagingItem

### Назначение

Тара или расходный материал.

Примеры:

```text
Банка 50 мл
Флакон 100 мл
Крышка
Этикетка
Пипетка
```

### Fields

```text
id
name
category
capacity_value
capacity_unit
unit
unit_cost
current_stock
minimum_stock
notes
status
created_at
updated_at
archived_at
```

### Relationships

```text
PackagingItem → Order[]
PackagingItem → StockMovement[]
PackagingItem → ProductionBatchPackaging[]
PackagingItem → PurchaseSuggestion[]
```

### Business rules

- `name` is required.
- `unit_cost` uses Decimal.
- `current_stock` cannot be negative.
- Packaging stock changes should go through StockMovement.
- Packaging can be archived if not needed anymore.
- Archived packaging used in existing orders/history remains readable.

### Audit

Log:

```text
packaging_item_created
packaging_item_updated
packaging_item_archived
```

---

## 6.12. StockMovement

### Назначение

Универсальное движение склада.

Все изменения остатков компонентов, партий и тары должны идти через StockMovement.

### Fields

```text
id
item_type
item_id
lot_id
movement_type
quantity
unit
reason
linked_order_id
linked_production_batch_id
source
created_at
created_by
```

### Item type values

```text
ingredient
ingredient_lot
packaging
```

### Movement type values

```text
inbound
outbound
manual_adjustment
expiration_writeoff
production_usage
reversal
correction
```

### Source values

```text
manual
production
import
system
restore
```

### Relationships

```text
StockMovement → Ingredient optional
StockMovement → IngredientLot optional
StockMovement → PackagingItem optional
StockMovement → Order optional
StockMovement → ProductionBatch optional
```

### Business rules

- `quantity` must be positive for movement record.
- Direction is determined by `movement_type`.
- Outbound must not create negative stock.
- Manual adjustment requires reason.
- Production usage must link to ProductionBatch.
- Import-created movement should link to import source/draft where possible.
- Reversal should reference original movement if implemented.

### Audit

StockMovement itself is part of audit trail, but important manual actions should also create AuditLog summary.

---

## 6.13. Order

### Назначение

Заказ клиента.

Заказ связывает клиента, рецепт, объем, тару, цену и будущий факт производства.

### Fields

```text
id
client_id
recipe_version_id
client_recipe_id
product_name
target_batch_grams
packaging_item_id
packaging_quantity
status
sale_price
estimated_cost
estimated_tax
estimated_margin
notes
ordered_at
planned_production_at
produced_at
delivered_at
created_at
updated_at
archived_at
```

### Status values

```text
new
waiting_for_materials
ready_to_produce
in_progress
produced
delivered
cancelled
archived
```

### Relationships

```text
Order → Client
Order → RecipeVersion optional
Order → ClientRecipe optional
Order → PackagingItem optional
Order → ProductionBatch optional
Order → ClientWish[]
Order → ClientFeedback[]
```

### Business rules

- `client_id` is required.
- Order must reference either `recipe_version_id` or `client_recipe_id`.
- It should not reference both unless implementation explicitly allows source trace.
- `target_batch_grams` is required and must be positive.
- Sale price can be optional at draft stage but needed for margin.
- Produced order cannot be produced again.
- Cancelled order should not create production write-off.
- Status changes must be explicit and audited.

### Audit

Log:

```text
order_created
order_updated
order_status_changed
order_cancelled
order_archived
```

---

## 6.14. ProductionBatch

### Назначение

Факт изготовления заказа.

ProductionBatch фиксирует, что именно было изготовлено, по какой формуле, в каком объеме, какими партиями компонентов и с какой себестоимостью.

### Fields

```text
id
order_id
recipe_version_id
client_recipe_id
final_batch_grams
component_cost
packaging_cost
other_cost
total_cost
sale_price
tax
margin
margin_percent
produced_at
notes
created_at
```

### Relationships

```text
ProductionBatch → Order
ProductionBatch → RecipeVersion optional
ProductionBatch → ClientRecipe optional
ProductionBatch → ProductionBatchIngredient[]
ProductionBatch → ProductionBatchPackaging[]
ProductionBatch → StockMovement[]
```

### Business rules

- `order_id` is required.
- Only one active ProductionBatch per order unless partial production is explicitly implemented later.
- Creation must be transactional with stock movements.
- Store snapshot of cost and consumed materials.
- Do not recalculate historical ProductionBatch silently.
- Production requires explicit user confirmation.
- Production cannot complete if blocking readiness issues exist, unless explicit override policy is later added.

### Financial calculation and tax snapshot semantics — decided, not implemented

Decided in `CR-007` (the setting) and `CR-008` (the calculation and the snapshots). Durable contracts: `docs/settings.md` and `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

**Current state.** On merged `main`, production readiness estimates `estimated_tax`, `estimated_margin`, and `estimated_margin_percent` (`C2-I`, PR #151). `C2-II` — the transactional snapshots, the two rate-snapshot columns below, migration `0019_production_batch_tax_rate_snapshots`, the required confirmation context, and `409 tax_rate_context_stale` — is merged as PR #152 and is `DONE — MERGED AND EXACT-HEAD VERIFIED`. `C2-III` was subdivided into `C2-III-A` (Order and `ProductionBatch` financial presentation, merged as PR #154) and `C2-III-B` (snapshot-backed reports and report documents, merged as PR #157, merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`); both are `DONE — MERGED AND EXACT-HEAD VERIFIED`. **Reports are snapshot-backed and C2 is `COMPLETED`.**

#### Calculation formulas (`CR-008`)

```text
tax_amount     = ROUND_MONEY(sale_price × tax_rate_percent / 100)
margin         = ROUND_MONEY(sale_price - total_cost - tax_amount)
margin_percent = ROUND_PERCENT(margin / sale_price × 100)
```

- `Decimal` only, never binary float at any intermediate step;
- the rate is a percentage, not a coefficient — `6.00` means `6%` — and is always divided by `100`;
- money quantum `0.01` and percentage quantum `0.01`, both `ROUND_HALF_UP`, rounding only the final amount of each formula;
- tax is deducted from gross revenue and never added on top of the sale price;
- margin may be positive, zero, or negative, and a negative margin — or a negative margin percent — is never clamped;
- margin percent is calculated only when margin is available and the sale price is greater than zero.

#### Availability matrix (`CR-008`)

| Sale price | Total cost | Tax rate | Tax | Margin | Margin % | Status |
|---|---|---|---|---|---|---|
| present, `> 0` | present | configured | available | available | available | `available` |
| present, `= 0` | present | configured | `0.00` | available | unavailable | `partial` |
| present | missing | configured | available | unavailable | unavailable | `partial` |
| present | present | missing | unavailable | unavailable | unavailable | `unavailable` |
| missing | any | any | unavailable | unavailable | unavailable | `unavailable` |
| any | any | invalid persisted value | unavailable | unavailable | unavailable | `unavailable` |

A configured `0.00` is configured, not missing. No missing input ever becomes zero. Physical production is never blocked by any row of this matrix.

#### No valid configured tax-rate context

**`no valid configured tax-rate context`** covers two backend states: no `default_tax_rate` row exists, or the persisted value exists but is invalid and cannot be safely interpreted as the canonical C1 percentage.

| Backend state | Readiness warning | `tax_rate_percent` | `tax_rate_effective_at` | Status | Tax / margin / margin % | Physical production |
|---|---|---|---|---|---|---|
| row absent | `tax_rate_missing` | `null` | `null` | `unavailable` | `null` | not blocked |
| value invalid | `tax_rate_invalid` | `null` | `null` | `unavailable` | `null` | not blocked |

The two states stay distinguishable through the warning code, but produce the same authoritative financial context. The invalid case must **not** also emit `tax_rate_missing`, and must not produce an unhandled HTTP `500`. The raw invalid value is never returned as the authoritative rate and is never normalized, coerced, rounded, treated as zero, copied into a readiness DTO, copied into a confirmation request, or copied into a `ProductionBatch` snapshot.

**Invariant.** An absent or invalid tax-rate setting may make financial values unavailable, but it must not by itself block physical production.

#### Existing readiness field mapping (`C2-I`)

The existing `POST /api/orders/{order_id}/check-production-readiness` response is extended additively. `estimated_cost`, `estimated_tax`, and `estimated_margin` already exist and are **reused** — `estimated_tax` and `estimated_margin` are activated, not duplicated. `C2-I` adds only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status`. `estimated_total_cost` is not authorized, and no alias of an existing field is authorized.

Financial warnings reuse the existing `ProductionReadinessIssue` structure and stay non-blocking. `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` are preserved unchanged; `CR-008` adds only `margin_percent_unavailable_zero_sale_price` and `tax_rate_invalid`.

#### ProductionBatch snapshot fields

| Field | Status | Meaning |
|---|---|---|
| `sale_price` | exists | taxable-base snapshot |
| `total_cost` | exists | actual production total-cost snapshot |
| `tax_rate_percent_snapshot` | nullable, added by `C2-II` migration `0019` | exact configured percentage used at confirmation |
| `tax_rate_effective_at_snapshot` | nullable, added by `C2-II` migration `0019` | exact backend effective timestamp used |
| `tax` | exists | final rounded tax-amount snapshot |
| `margin` | exists | final rounded margin snapshot |
| `margin_percent` | exists | final rounded margin-percent snapshot |

Rules:

- the MVP taxable base is exactly the order sale price, so no separate `taxable_amount_snapshot` is required;
- the existing financial fields are **reused**; duplicate monetary snapshot fields such as `sale_price_snapshot`, `total_cost_snapshot`, `tax_amount_snapshot`, or `margin_amount_snapshot` are **not** authorized;
- the two columns are nullable for backward compatibility and are **never backfilled** with the current rate;
- rows produced before the snapshot fields existed stay unknown and map to `null`; the merged `C2-III-A` presentation displays them as `Недоступно`, never as a fabricated `0.00`;
- changing the current tax setting never changes an existing ProductionBatch row, an existing report snapshot, a prior audit record, or a previously generated document;
- reports and exports read the stored snapshots and must not recalculate historical tax with the current setting;
- an order created before a rate change but produced after it uses the rate active at production confirmation;
- future margin must use the persisted rounded tax snapshot, not a freshly recalculated current-rate value;
- the columns were added by exactly one additive nullable migration, `0019_production_batch_tax_rate_snapshots`, under the existing user-mode backup-before-migration safety flow.

#### Required confirmation tax context (`C2-II`)

The production-confirmation request always carries both `expected_tax_rate_percent` and `expected_tax_rate_effective_at`. They are **required but nullable** and are declared without default values. Only two pairs are valid:

1. a canonical two-decimal percentage string with a canonical `YYYY-MM-DDTHH:MM:SSZ` timestamp;
2. explicit `null` with explicit `null`, meaning **the latest readiness result observed no valid configured tax rate** — which covers both a missing setting row and an invalid persisted setting, not only an absent row.

**Omitting a key is not equivalent to explicit `null/null`** — omission means an invalid or outdated client contract and is rejected with HTTP `422` and the stable code `tax_rate_context_required`, while a partial-null, malformed, non-canonical, or out-of-range context, or a non-canonical timestamp, is rejected with `invalid_tax_rate_context`.

`C2-II` re-reads the current canonical setting **inside the same production transaction**, through a bounded read-only `connection`-aware extension of the `C1` tax-rate service, never through a second independent connection and never by parsing raw `AppSetting` values in the confirmation service. It reduces the current state to a **valid context** (canonical percentage + canonical API timestamp) or a **no-valid-rate context** (`null` + `null`, from a missing row or an invalid value) and compares:

| Expected context | Current backend context | Result |
|---|---|---|
| same valid pair | same valid pair | continue |
| valid pair | different valid pair | `409 tax_rate_context_stale` |
| valid pair | missing | `409 tax_rate_context_stale` |
| valid pair | invalid | `409 tax_rate_context_stale` |
| `null/null` | valid pair | `409 tax_rate_context_stale` |
| `null/null` | missing | continue |
| `null/null` | invalid | continue |

**Missing → invalid and invalid → missing are deliberately not stale conflicts**, because both produce the same financial result: no rate snapshot, no tax, no margin, no margin percent. A stale conflict writes nothing at all. The code `tax_rate_context_stale` supersedes the earlier illustrative name `financial_settings_changed` used while `CR-007` was being decided.

An accepted no-valid-rate confirmation persists `tax_rate_percent_snapshot = null`, `tax_rate_effective_at_snapshot = null`, `tax = null`, `margin = null`, `margin_percent = null`, while every physical production snapshot is written normally. Confirmation never repairs, clears, rewrites, or audits the invalid setting, and never persists the raw invalid value.

**Timestamp formats.** Database persistence — `AppSetting.updated_at` and `tax_rate_effective_at_snapshot` — uses `YYYY-MM-DD HH:MM:SS` UTC SQLite text with no `T`, no `Z`, and no offset. The API and confirmation-context representation is `YYYY-MM-DDTHH:MM:SSZ`. Local-time values, arbitrary offsets, fractional seconds, a space instead of `T`, and a missing `Z` are rejected with `422 invalid_tax_rate_context`. The API normalizes the stored snapshot and never exposes the raw SQLite form.

#### Transactional snapshot immutability

All financial snapshots are written **once**, inside the same transaction as the `ProductionBatch`, the component movements, the packaging movements, the Order update, and the production audit records. Any failure rolls back every one of them, and a partially confirmed production must never exist. Once committed, a snapshot is never recalculated — not by a later rate change, not by reports, and not by a future replacement of the simplified tax model.

### Audit

Log:

```text
production_batch_created
production_confirmed
```

---

## 6.15. ProductionBatchIngredient

### Назначение

Snapshot строки компонента, фактически использованного при производстве.

### Fields

```text
id
production_batch_id
ingredient_id
ingredient_lot_id
ingredient_name_snapshot
lot_number_snapshot
required_quantity
consumed_quantity
unit
unit_cost_snapshot
total_cost_snapshot
expiration_date_snapshot
created_at
```

### Relationships

```text
ProductionBatchIngredient → ProductionBatch
ProductionBatchIngredient → Ingredient
ProductionBatchIngredient → IngredientLot
```

### Business rules

- Must preserve snapshot values.
- Must link to lot used.
- Consumed quantity must match StockMovement.
- Unit cost snapshot must not change if lot price changes later.

---

## 6.16. ProductionBatchPackaging

### Назначение

Snapshot тары, фактически использованной при производстве.

### Fields

```text
id
production_batch_id
packaging_item_id
packaging_name_snapshot
quantity
unit
unit_cost_snapshot
total_cost_snapshot
created_at
```

### Relationships

```text
ProductionBatchPackaging → ProductionBatch
ProductionBatchPackaging → PackagingItem
```

### Business rules

- Must preserve snapshot.
- Consumed packaging must match StockMovement.
- Unit cost snapshot must not change historically.

---

## 6.17. Alert

### Назначение

Предупреждение для пользователя.

### Fields

```text
id
type
severity
message
related_entity_type
related_entity_id
recommended_action
status
created_at
resolved_at
dismissed_at
```

### Type values

```text
low_ingredient_stock
low_packaging_stock
ingredient_expiration_soon
ingredient_expired
insufficient_materials_for_order
insufficient_packaging_for_order
missing_density
recipe_total_invalid
archived_ingredient_in_recipe
backup_reminder
```

### Severity values

```text
info
warning
critical
blocking
```

### Status values

```text
open
resolved
dismissed
```

### Relationships

```text
Alert → related entity by type/id
```

### Business rules

- Alert generation should be idempotent/deduplicated.
- Alert must have human-readable message.
- Alert must suggest next action.
- Resolved alert should not immediately reappear unless condition still exists and regeneration policy says so.
- Dashboard displays open alerts.

### Audit

Resolving/dismissing alerts can be audited if important.

---

## 6.18. PurchaseSuggestion

### Назначение

Предложение закупки.

### Fields

```text
id
item_type
item_id
recommended_quantity
unit
reason
status
notes
created_at
updated_at
resolved_at
```

### Item type values

```text
ingredient
packaging
```

### Reason values

```text
below_minimum_stock
insufficient_for_order
predicted_shortage
expiration_replacement
manual
```

### Status values

```text
open
purchased
dismissed
archived
```

### Relationships

```text
PurchaseSuggestion → Ingredient optional
PurchaseSuggestion → PackagingItem optional
```

### Business rules

- Suggestion should explain why it exists.
- Duplicate suggestions should be avoided.
- Marking as purchased may guide user to create IngredientLot or packaging inbound movement.
- Should not automatically create stock unless user confirms.

### Audit

Log:

```text
purchase_suggestion_created
purchase_suggestion_updated
purchase_suggestion_marked_purchased
purchase_suggestion_dismissed
```

---

## 6.19. ImportSource

### Назначение

Загруженный файл импорта.

### Fields

```text
id
file_name
file_type
file_path
uploaded_at
status
raw_metadata
errors
created_at
updated_at
```

### File type values

```text
csv
xlsx
pdf
image
unknown
```

### Status values

```text
uploaded
parsed
failed
cancelled
applied
archived
```

### Relationships

```text
ImportSource → ImportDraft[]
```

### Business rules

- MVP supports CSV/XLSX.
- PDF/image are future and should not be trusted automatically.
- Source file should be stored in user data directory or temporary import storage.
- Failed parse should keep error summary.

---

## 6.20. ImportDraft

### Назначение

Черновик импорта перед применением данных.

### Fields

```text
id
import_source_id
target_entity_type
column_mapping
parsed_rows
validation_errors
status
created_at
updated_at
applied_at
cancelled_at
```

### Target entity values

```text
clients
ingredients
ingredient_lots
packaging
stock_balances
recipe_templates
```

### Status values

```text
draft
mapped
validated
has_errors
ready_to_apply
applied
cancelled
failed
```

### Relationships

```text
ImportDraft → ImportSource
```

### Business rules

- Cannot apply without preview.
- Cannot apply with blocking validation errors.
- Apply must be explicit user confirmation.
- Apply must be transactional.
- Validation errors must include row, column, value and human message.
- Applying import creates AuditLog.

### Audit

Log:

```text
import_draft_created
import_draft_validated
import_draft_applied
import_draft_cancelled
```

---

## 6.21. AuditLog

### Назначение

Журнал важных действий.

### Fields

```text
id
action
entity_type
entity_id
summary
source
created_at
metadata
```

### Source values

```text
manual
system
import
production
migration
backup
onboarding
restore
```

> **Persistence versus API name.** The database column created by `0001_infrastructure` and written by `AuditLogRepository.create_log` is **`actor_type`**. The durable domain and API name is **`source`**; the `C3-I` read model maps one to the other at read time. The column is not renamed, and no migration or backfill is authorized. Existing write call sites are not changed merely to rename this field.
>
> **Actual persisted values.** The vocabulary above is aspirational. Only **`system`** and **`user`** are actually written on merged `main`: `system` is the `create_log` default used by every call site except one, and `user` is written only for `tax_rate_setting_changed`. `manual`, `import`, `production`, `migration`, `backup` and `restore` are not persisted anywhere. `C3-I` presents what exists and routes anything else through the safe unknown-code label. Full inventory: `docs/audit-log.md` § 10.

### Business rules

- AuditLog should be append-only.
- Do not store full sensitive client notes by default.
- Store safe summaries.
- Metadata can contain technical details, but no secrets.
- Important business actions must create AuditLog.
- `metadata_json` is **never** returned by the read API. It is dominated by internal foreign-key IDs, enum codes and counters — exactly the class of value a non-technical user must not see — so the `C3-I` read model excludes it in full rather than field by field.
- The read surface is one endpoint, `GET /api/audit-logs`, defined in `docs/audit-log.md`. The former `GET /api/audit-logs/{id}` proposal is superseded for the MVP.

### Examples

```text
client_created
recipe_version_created
order_status_changed
production_confirmed
backup_created
settings_updated
```

---

## 6.22. AppSettings

### Назначение

Настройки приложения.

### Fields

```text
id
default_tax_rate
expiration_alert_days
low_stock_alert_enabled
backup_reminder_enabled
default_recipe_unit
app_version
schema_version
data_directory_path
created_at
updated_at
```

### Business rules

- `default_tax_rate` has **no default**. The former `tax_rate default is 0.06` rule is superseded by `CR-007`: the setting is a **percentage**, so `6.00` means `6%` and `0.06` would mean `0.06%`, and an unconfigured setting is `null`, which is never the same as `0.00`. Durable contract: `docs/settings.md`.
- Changes should be audited.
- `data_directory_path` should be visible to user but not casually editable without care.
- Settings should support future expansion.

---

## 6.23. OnboardingState

### Назначение

Состояние первого запуска и обучающего checklist.

### Fields

```text
id
first_run_completed
demo_data_created
checklist_hidden
completed_steps
backup_reminder_enabled
created_at
updated_at
```

### Completed steps

```text
add_first_ingredient
add_first_lot
add_first_packaging
create_first_recipe
create_first_client
create_first_client_recipe
create_first_order
run_first_production
create_first_backup
```

### Business rules

- First-run wizard uses this state.
- Checklist should auto-complete steps when real data appears.
- User can hide and restore checklist.
- Demo data must be clearly marked.

### Audit

Log:

```text
onboarding_completed
onboarding_checklist_hidden
demo_data_created
demo_data_removed
```

---

## 6.24. HelpArticle

### Назначение

Статья встроенной офлайн-справки.

Может храниться как Markdown-файл, а не обязательно в БД.

### Fields

```text
slug
title
body
related_screen
order
status
```

### Examples

```text
how-to-create-recipe
how-to-add-ingredient
how-to-add-lot
how-to-create-client
how-to-create-client-recipe
how-to-create-order
how-to-produce-order
how-to-create-backup
what-is-density
what-is-lot
what-is-client-recipe
what-is-recipe-version
```

### Business rules

- Help must work offline.
- User-facing help should be simple and Russian.
- Help content should not be mixed with developer docs.

---

## 6.25. BackupRecord

### Назначение

Запись о созданной резервной копии.

### Fields

```text
id
file_path
created_at
reason
app_version
schema_version
status
notes
```

### Reason values

```text
manual
before_migration
scheduled_reminder
before_restore
```

### Status values

```text
created
failed
verified
deleted
```

### Business rules

- Backup must be stored in user data directory.
- Before migration, backup is mandatory.
- Backup action should be audited.
- User must be able to see where backup file is located.

### Audit

Log:

```text
backup_created
backup_failed
backup_verified
```

---

## 6.26. UpdateLog

### Назначение

Лог обновления приложения и миграций.

### Fields

```text
id
from_app_version
to_app_version
from_schema_version
to_schema_version
backup_id
started_at
finished_at
status
error_message
```

### Status values

```text
started
completed
failed
rolled_back
```

### Business rules

- Before schema migration, create BackupRecord.
- UpdateLog should link to backup.
- If migration fails, user must see understandable error.
- Do not destroy old DB silently.

### Audit

Log:

```text
update_started
update_completed
update_failed
```

---

## 6.27. Attachment

### Назначение

Файл, связанный с сущностью.

Например:

- фото упаковки;
- фото продукта;
- документ поставщика;
- сертификат;
- PDF;
- скриншот.

### Fields

```text
id
entity_type
entity_id
file_name
file_type
file_path
created_at
notes
status
```

### Business rules

- Attachment file should live in user data directory.
- Attachment UI can be v2.
- Do not store large binary blobs directly in SQLite unless intentionally decided.
- Do not delete attachment files without confirmation.

---

# 7. Enums and shared dictionaries

---

## 7.1. Units

```text
g
ml
pcs
```

Future:

```text
kg
l
drop
```

Do not add future units without testing calculation behavior.

---

## 7.2. Recipe phases

Suggested values:

```text
water_phase
oil_phase
active_phase
cooldown_phase
fragrance_phase
preservative_phase
other
```

User-facing labels must be Russian.

---

## 7.3. Ingredient roles

Suggested values:

```text
water
oil
butter
emulsifier
thickener
preservative
active
fragrance
colorant
surfactant
humectant
other
```

---

## 7.4. Common statuses

Use explicit statuses instead of booleans when business state matters.

Examples:

```text
active
draft
archived
superseded
depleted
expired
cancelled
produced
delivered
```

---

# 8. Calculation domain rules

---

## 8.1. Percent to grams

```text
required_grams = final_batch_grams * percent / 100
```

Example:

```text
153g * 5% = 7.65g
```

---

## 8.2. Recipe total percent

```text
total_percent = sum(percent)
```

States:

```text
valid_100
below_100
above_100
```

Do not silently normalize percentages.

---

## 8.3. ml to grams

```text
grams = ml * density
```

If density is missing:

```text
return warning
mark calculation approximate
do not hide warning during production
```

---

## 8.4. Cost

```text
component_cost = sum(consumed_quantity * lot_unit_cost)
packaging_cost = sum(packaging_quantity * packaging_unit_cost)
total_cost = component_cost + packaging_cost + other_cost
tax = ROUND_MONEY(sale_price * tax_rate_percent / 100)
margin = ROUND_MONEY(sale_price - total_cost - tax)
margin_percent = ROUND_PERCENT(margin / sale_price * 100)
```

All money calculations use Decimal, never binary float at any intermediate step.

`tax_rate_percent` is a **percentage** in the range `0.00`–`100.00`, not a coefficient: `6.00` means `6%`, and the percentage is always divided by `100`. Only the final amount of each formula is rounded — money at quantum `0.01`, percentage at quantum `0.01`, both `ROUND_HALF_UP`. Tax is deducted from gross revenue, never added on top.

A missing rate makes tax — and any tax-dependent margin — **unavailable, never zero**; a configured `0.00` is a real value producing tax `0.00`. Margin is unavailable when the sale price, the total cost, or the tax amount is unavailable, and margin percent is calculated only when margin is available and the sale price is greater than zero. A negative margin or margin percent is valid and is never clamped. See `CR-007`, `CR-008`, `docs/settings.md`, and `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

---

## 8.5. FEFO

For ingredient lot selection use:

```text
First Expired, First Out
```

Lots with nearest expiration are used first.

---

# 9. Required indexes and uniqueness suggestions

Exact indexes are implementation details, but these are recommended.

```text
Client.phone
Client.first_name + last_name
RecipeTemplate.name
RecipeVersion.recipe_template_id + version_number
ClientRecipe.client_id
Ingredient.name
IngredientLot.ingredient_id
IngredientLot.expiration_date
StockMovement.created_at
Order.client_id
Order.status
Order.planned_production_at
Alert.status
Alert.type
PurchaseSuggestion.status
AuditLog.created_at
```

Potential unique constraints:

```text
RecipeVersion(recipe_template_id, version_number)
Ingredient normalized name if feasible
HelpArticle.slug
```

Do not over-constrain user-entered names too early if it hurts usability.

---

# 10. Data lifecycle

---

## 10.1. Draft

Entity is being created or not ready for production.

Examples:

```text
RecipeVersion draft
ClientRecipe draft
Order new
ImportDraft draft
```

---

## 10.2. Active

Entity is usable in normal workflows.

Examples:

```text
Client active
Ingredient active
RecipeVersion active
ClientRecipe active
```

---

## 10.3. Historical

Entity is preserved for old orders and production.

Examples:

```text
RecipeVersion superseded
ProductionBatch created
StockMovement created
AuditLog created
```

---

## 10.4. Archived

Entity is hidden from normal active lists but remains readable.

Examples:

```text
Client archived
Ingredient archived
RecipeTemplate archived
Order archived
```

---

# 11. Test requirements mapped to domain model

Codex must add or update tests when implementing these entities.

## 11.1. Client

- create client;
- update client;
- archive client;
- sensitive notes not fully logged.

## 11.2. Recipe

- create RecipeTemplate;
- create RecipeVersion;
- add RecipeIngredient;
- validate percent total;
- calculate grams;
- missing density warning.

## 11.3. ClientRecipe

- create from RecipeVersion;
- source RecipeVersion unchanged;
- calculate ClientRecipe;
- link to Client.

## 11.4. ClientWish / ClientFeedback

- create wish;
- update status;
- create feedback;
- link to order/client recipe;
- audit without sensitive leakage.

## 11.5. Inventory

- create Ingredient;
- create IngredientLot;
- reject invalid quantity;
- create PackagingItem;
- create StockMovement;
- prevent negative stock.

## 11.6. Production

- readiness success;
- readiness failure;
- FEFO selection;
- transactional production;
- cannot produce twice;
- rollback on failure;
- snapshots stored.

## 11.7. Import

- create ImportSource;
- create ImportDraft;
- validate rows;
- reject invalid rows;
- apply only after confirmation;
- apply in transaction.

## 11.8. Backup/update

- create BackupRecord;
- backup file exists;
- UpdateLog created;
- backup before migration.

---

# 12. What Codex must not do

Codex must not:

```text
flatten RecipeTemplate/RecipeVersion/ClientRecipe into one Recipe table;
change stock without StockMovement;
implement production without transaction;
write import directly to production tables;
silently normalize recipe percentages;
silently treat 1 ml as 1 g without warning;
hard-delete business entities with history;
store user data inside repo/app package;
write sensitive client notes into logs;
show technical IDs or stack traces to user;
add cloud/mobile/OCR/AI features without explicit scope.
```

---

# 13. MVP domain acceptance checklist

MVP domain model is sufficient when the system can represent:

```text
[ ] Client
[ ] ClientWish
[ ] ClientFeedback
[ ] RecipeTemplate
[ ] RecipeVersion
[ ] RecipeIngredient
[ ] ClientRecipe
[ ] ClientRecipeIngredient
[ ] Ingredient
[ ] IngredientLot
[ ] PackagingItem
[ ] StockMovement
[ ] Order
[ ] ProductionBatch
[ ] ProductionBatchIngredient
[ ] ProductionBatchPackaging
[ ] Alert
[ ] PurchaseSuggestion
[ ] ImportSource
[ ] ImportDraft
[ ] AuditLog
[ ] AppSettings
[ ] OnboardingState
[ ] BackupRecord
[ ] UpdateLog
[ ] HelpArticle
[ ] Attachment placeholder or future-safe path
```

---

## 14. Final domain statement

The domain model must support the real working loop:

```text
A client has needs and wishes.
The maker creates or adapts a formula.
The formula becomes an order.
The order becomes production.
Production consumes real lots and packaging.
The system preserves cost, history and feedback.
The next formula improves based on the client history.
```

If the model supports this loop safely and traceably, it matches the product.
