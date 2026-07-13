# cosmetic-workshop-os — Итоговый roadmap реализации через Codex

Проект: **cosmetic-workshop-os**  
Клиентское название: **Мастерская косметолога**  
Тип продукта: **local-first web-приложение для учета рецептур, клиентов, запасов, заказов, производства, алертов и закупок косметической мастерской**  
Документ: **docs/roadmap.md**  
Версия: **1.0 final draft**  
Формат реализации: **Codex + GitHub + поэтапные PR**

---

## 1. Назначение roadmap

Этот roadmap описывает итоговый порядок реализации проекта через Codex.

Документ учитывает:

- рецептурное ядро;
- индивидуальные рецепты клиентов;
- клиентские пожелания и обратную связь;
- склад компонентов и тары;
- партии компонентов и сроки годности;
- заказы;
- производство;
- автоматическое списание;
- себестоимость, налог, маржу;
- алерты;
- закупочный список;
- импорт Excel/CSV;
- будущий импорт PDF/images через OCR;
- backup/export;
- local deployment на MacBook;
- user data directory;
- first-run onboarding;
- guided checklist;
- demo mode;
- help center;
- UI/UX contract;
- update safety;
- remote install checklist;
- будущий путь к cloud/mobile/OCR.

Главная цель roadmap: вести проект так, чтобы Codex не строил “комбайн сразу”, а создавал надежную систему маленькими проверяемыми PR.

---

## Current execution plan

The strategic roadmap remains the product-level source of scope and sequencing.

The current short-horizon implementation sequence, audit-driven hardening slices, unfinished MVP obligations, and release gates are maintained in:

- [Implementation plan](implementation-plan.md)

## 2. Главный продуктовый принцип

Пользователь получает не GitHub-репозиторий, не техническую админку и не таблицу рецептов.

Пользователь получает локальную рабочую систему, которую можно:

```text
открыть
→ понять
→ настроить
→ вести рецепты
→ вести клиентов
→ вести индивидуальные формулы
→ вести заказы
→ списывать склад
→ получать алерты
→ делать закупки
→ делать backup
→ обновлять без потери данных
```

---

## 3. Обязательные документы проекта

Перед началом разработки в репозитории должны быть или постепенно появиться:

```text
AGENTS.md
README.md

docs/
  product-spec.md
  roadmap.md
  architecture.md
  domain-model.md
  ui-ux-guidelines.md
  ui-ux-contract.md
  import-format.md
  backup-and-restore.md
  local-install.md
  user-install.md
  remote-install-checklist.md
  update-guide.md
  user-guide.md
  mvp-smoke-checklist.md
```

`AGENTS.md` — главный системный контракт для Codex.

`docs/architecture.md` — архитектурный контракт.

`docs/roadmap.md` — этот документ.

---

## 4. Архитектурные инварианты

Эти правила нельзя нарушать ни на одном этапе.

### 4.1. Local-first

MVP работает локально на MacBook без обязательного интернета.

```text
Packaged local app
→ Local launcher
→ Browser UI
→ Local backend API
→ SQLite
→ User data directory
```

### 4.2. Пользовательские данные отдельно от кода

Данные не должны храниться в папке приложения или репозитория.

Рекомендуемая структура:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

### 4.3. Рецепты не плоские

Нельзя делать просто одну сущность `Recipe`.

Нужна структура:

```text
RecipeTemplate
→ RecipeVersion
→ ClientRecipe
```

### 4.4. Индивидуальные рецепты обязательны

Индивидуальный рецепт клиента — first-class сущность, а не заметка.

### 4.5. Пожелания и обратная связь клиента обязательны

Нужны сущности:

```text
ClientWish
ClientFeedback
```

Цикл:

```text
Order
→ Feedback
→ Wish
→ New client recipe version/copy
→ Next order
```

### 4.6. Склад через партии и движения

Нельзя хранить только “остаток компонента”.

Нужно:

```text
Ingredient
→ IngredientLot
→ StockMovement
```

### 4.7. Производство transactional

Производство заказа должно создавать:

```text
ProductionBatch
StockMovement for ingredients
StockMovement for packaging
Order status update
AuditLog
```

Если что-то падает, не должно быть частичного списания.

### 4.8. Импорт только через черновики

```text
ImportSource
→ ImportDraft
→ validation
→ preview
→ confirmation
→ apply
```

### 4.9. UI не техническая админка

Каждый экран должен быть понятным для нетехнического пользователя.

Нужны:

- empty states;
- подсказки;
- человекопонятные ошибки;
- next action;
- guided checklist;
- help center.

### 4.10. Обновления безопасны

Перед миграцией базы создается backup.

```text
new app version
→ detect schema migration
→ create backup
→ run migration
→ write UpdateLog
→ open app
```

---

## 5. Итоговая последовательность PR

```text
PR0   Docs contract
PR1   App shell
PR2   DB + settings + audit
PR3   Units/categories/Decimal helpers

D1    User data directory
D2    Local launcher
O1    First-run wizard
O2    Empty states + contextual help
UX1   Human-friendly UI system contract

PR4   Backup foundation
PR5   Ingredients/lots backend
PR6   Packaging/stock movements backend
PR7   Inventory UI

PR8   Recipe models backend
PR9   Recipe calculation service
PR10  Recipe UI

PR11  Clients
PR12  Client recipes
PR12b Client wishes and feedback

PR13  Orders backend
PR14  Orders UI

PR15  Production readiness
PR16  Production write-off
PR17  Production UI

PR18  Alerts
PR19  Purchase suggestions
PR20  Dashboard

O3    Guided setup checklist
O4    Demo data mode
O5    In-app help center

PR21  Import backend
PR22  Import UI
PR23  Export/restore

PR24  Reports
PR25  PDF

PR26  Settings UI
PR27  Audit viewer

D3    macOS package MVP
D4    Update safety
D5    Remote install checklist

PR28  Demo/user guide/smoke
PR29  MVP hardening

V2+   Cloud/mobile/OCR/attachments/certifications/advanced analytics
```

---

# PHASE 0 — Project contract and documentation

## PR0 — Project documentation contract

### Goal

Создать проектный контракт, чтобы Codex понимал продукт, архитектуру, границы MVP, roadmap и правила разработки.

### Scope

Добавить:

```text
AGENTS.md
README.md
docs/product-spec.md
docs/roadmap.md
docs/architecture.md
docs/domain-model.md
docs/ui-ux-guidelines.md
docs/import-format.md
docs/backup-and-restore.md
```

### Required content

`README.md`:

- что это за проект;
- для кого он;
- как запустить dev-режим;
- как устроен local-first подход;
- текущий статус проекта.

`AGENTS.md`:

- роль Codex;
- архитектурные правила;
- non-goals;
- расчетные правила;
- UI/UX правила;
- PR workflow;
- testing requirements.

`docs/architecture.md`:

- local launcher;
- user data directory;
- backend/frontend/domain/database;
- onboarding;
- help layer;
- update safety;
- future cloud/mobile/OCR.

### Non-goals

- Не писать production-код.
- Не создавать модели БД.
- Не создавать UI.

### Acceptance criteria

- Документы созданы.
- AGENTS.md является главным контрактом для Codex.
- Архитектура и roadmap согласованы.
- В документах есть MVP scope и non-goals.

---

# PHASE 1 — Technical foundation

## PR1 — Bootstrap backend and frontend shell

### Goal

Создать минимальный запускаемый проект с backend, frontend и базовой навигацией.

### Backend scope

- FastAPI app.
- Health endpoint:

```text
GET /api/health
```

- Структура backend:

```text
backend/app/
  api/
  domain/
  services/
  repositories/
  models/
  schemas/
  tests/
```

### Frontend scope

- React + TypeScript + Vite.
- Базовый layout.
- Навигация:

```text
Главная
Рецепты
Клиенты
Заказы
Запасы
Тара
Закупки
Производство
Отчеты
Импорт
Настройки
Помощь
```

- Dashboard placeholder.
- Health status from backend.

### Tests

- Backend health endpoint test.
- Frontend build.

### Non-goals

- Нет бизнес-моделей.
- Нет склада.
- Нет рецептов.
- Нет packaging.

### Acceptance criteria

- Backend запускается.
- Frontend запускается.
- Frontend получает health status.
- Навигация отображается.

---

## PR2 — Database, migrations, settings and AuditLog foundation

### Goal

Заложить БД, миграции, настройки приложения и AuditLog.

### Backend scope

- SQLite connection.
- SQLAlchemy.
- Alembic.
- `app_settings`.
- `audit_logs`.
- Settings service.
- Audit service.

### AppSettings MVP fields

```text
tax_rate default 0.06
expiration_alert_days default 30
low_stock_alert_enabled default true
backup_reminder_enabled default true
default_recipe_unit default grams
app_version
schema_version
```

### AuditLog MVP fields

```text
id
action
entity_type
entity_id
summary
source
created_at
```

### API

```text
GET /api/settings
PATCH /api/settings
GET /api/audit-logs
```

`GET /api/audit-logs` может быть ограниченным или dev-only до PR27, но базовое чтение полезно для проверки.

### Tests

- Migration applies.
- Settings can be read.
- Settings can be updated.
- Audit log can be created.
- Sensitive notes are not required in audit summary.

### Non-goals

- Нет полноценного Audit UI.
- Нет авторизации.
- Нет бизнес-сущностей.

### Acceptance criteria

- База создается.
- Миграции работают.
- Настройки сохраняются.
- AuditLog работает.

---

## PR3 — Units, categories and Decimal helpers

### Goal

Создать общие доменные примитивы и расчетную основу.

### Backend scope

Справочники/enum:

```text
units: g, ml, pcs
ingredient categories
ingredient roles
recipe categories
recipe phases
packaging categories
order statuses
movement types
alert types
wish statuses
feedback types if needed
```

### Decimal rules

Использовать Decimal для:

- процентов;
- граммов;
- денег;
- плотности;
- себестоимости;
- налога;
- маржи.

Рекомендуемое округление:

```text
grams: 0.01
percent: 0.001
money: 0.01
density: 0.0001
```

### Frontend scope

- Shared label mapping на русском.
- Human-readable labels для enum.

### Tests

- Decimal helper.
- Rounding helper.
- Enum labels available.

### Non-goals

- Нет рецептов.
- Нет склада.

### Acceptance criteria

- Общие справочники доступны.
- Расчеты не используют float для критичных данных.
- UI получает понятные labels.

---

# DEPLOYMENT LINE 1 — Local runtime before business complexity

## D1 — User data directory

### Goal

Отделить пользовательские данные от кода приложения.

### Scope

- Создать сервис определения user data directory.
- Создавать структуру:

```text
data/
backups/
exports/
attachments/
logs/
```

- SQLite database path должен быть в `data/`.
- Добавить настройки/endpoint для просмотра data path.
- Добавить проверки прав записи.
- Добавить понятные ошибки, если папка недоступна.

### Recommended default

```text
~/Documents/Мастерская косметолога/
```

### Tests

- Data directory created.
- Database path resolves outside repo/app folder.
- Missing folders are created.
- No write permission returns human-readable error.

### Non-goals

- Нет полноценного app packaging.
- Нет cloud sync.

### Acceptance criteria

- База не лежит в репозитории.
- Обновление приложения не должно затрагивать user data.
- Пользователь может увидеть, где лежат данные.

---

## D2 — Local launcher

### Goal

Сделать локальный запуск без ручных команд для user mode.

### Scope

- Local launcher script/app wrapper.
- Проверка data directory.
- Проверка базы.
- Применение миграций.
- Запуск backend на localhost.
- Открытие браузера.
- Проверка занятого порта.
- Понятная ошибка, если приложение уже запущено или порт занят.

### Flow

```text
Open app
→ launcher checks data dir
→ launcher checks db
→ migrations
→ starts backend
→ opens browser
```

### Tests

- Launcher starts backend.
- Browser URL generated.
- Existing running instance handled.
- Port conflict handled.

### Non-goals

- Нет .dmg.
- Нет auto-update.
- Нет signing.

### Acceptance criteria

- Приложение можно запустить одной командой/одним launcher.
- Пользовательскому режиму не нужен dev server.
- Backend слушает только localhost.

---

# ONBOARDING LINE 1 — First user experience

## O1 — First-run wizard

### Goal

Сделать первый запуск понятным для нетехнического пользователя.

### Scope

Создать `OnboardingState`.

Fields:

```text
first_run_completed
demo_data_created
checklist_hidden
completed_steps
backup_reminder_enabled
created_at
updated_at
```

Wizard steps:

```text
1. Добро пожаловать
2. Где хранить данные
3. Налоговая ставка
4. Напоминание о backup
5. Создать демо-данные
6. Начать работу
```

### API

```text
GET /api/onboarding/state
POST /api/onboarding/complete-first-run
PATCH /api/onboarding/state
```

### Frontend

- `/onboarding`
- automatic redirect on first run
- save settings

### Tests

- First run state created.
- Completing wizard saves settings.
- Returning user does not see wizard again.

### Non-goals

- No demo data yet, only placeholder flag unless O4 is in same scope.
- No advanced tour.

### Acceptance criteria

- Первый запуск не открывает пустую систему.
- Пользователь понимает, что делать.
- Настройки сохраняются.

---

## O2 — Empty states and contextual help

### Goal

Сделать интерфейс понятным даже при пустой базе.

### Scope

Добавить reusable UI components:

```text
EmptyState
FieldHint
Tooltip
HumanErrorMessage
NextActionBlock
```

Пустые состояния для:

- recipes;
- clients;
- orders;
- stock;
- packaging;
- purchases;
- reports;
- import.

Подсказки для:

- density;
- minimum stock;
- lot;
- recipe version;
- client recipe;
- expiration date;
- margin;
- production batch.

### Tests

- Frontend build.
- Key pages render empty states.

### Non-goals

- No full help center yet.
- No guided checklist yet.

### Acceptance criteria

- “Нет данных” заменено на понятные объяснения.
- Каждый пустой экран предлагает следующий шаг.
- Сложные поля имеют подсказки.

---

## UX1 — Human-friendly UI system and UX contract

### Goal

Зафиксировать и реализовать базовый UI/UX слой, чтобы Codex не строил техническую админку.

### Scope

Добавить:

```text
docs/ui-ux-contract.md
frontend/shared/ui/
frontend/shared/status-badges/
frontend/shared/error-messages/
frontend/shared/confirmation-dialogs/
frontend/shared/form-hints/
```

### UX rules

- technical IDs hidden;
- errors human-readable;
- every destructive action requires confirmation;
- every warning explains reason;
- every page has next action;
- status labels in Russian;
- visual severity for alerts;
- forms grouped by meaning;
- advanced fields can be collapsed.

### Tests

- Build.
- Snapshot/simple render tests if available.

### Non-goals

- No full design system.
- No advanced visual polish.

### Acceptance criteria

- UI has consistent components.
- Statuses and errors are understandable.
- Architecture has a UI contract.

---

# PHASE 2 — Backup foundation before business data grows

## PR4 — Backup foundation

### Goal

Заложить backup до появления большого объема данных.

### Scope

- BackupService.
- BackupRecord.
- Manual backup endpoint:

```text
POST /api/backups
GET /api/backups
```

- Backup folder inside user data directory.
- Backup action logged.
- Basic backup UI in settings.

### Backup contents

MVP at this stage:

- database file or JSON export of current DB;
- app version;
- schema version;
- created_at.

### Tests

- Backup file created.
- Backup record saved.
- AuditLog written.

### Non-goals

- Restore can be deferred.
- No cloud backup.

### Acceptance criteria

- Пользователь может создать backup.
- Backup не требует интернета.
- Backup лежит в понятной папке.

---

# PHASE 3 — Inventory foundation

## PR5 — Ingredients and IngredientLots backend

### Goal

Создать backend для компонентов и партий.

### Models

```text
Ingredient
IngredientLot
```

### Ingredient fields

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
```

### IngredientLot fields

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
```

### API

```text
GET /api/ingredients
POST /api/ingredients
GET /api/ingredients/{id}
PATCH /api/ingredients/{id}
POST /api/ingredients/{id}/archive

GET /api/ingredient-lots
POST /api/ingredient-lots
GET /api/ingredient-lots/{id}
PATCH /api/ingredient-lots/{id}
```

### Rules

- Remaining quantity cannot be negative.
- Remaining quantity cannot exceed initial quantity.
- Ingredient cannot be hard-deleted if used.
- Archive instead of delete.

### Tests

- Create ingredient.
- Update ingredient.
- Archive ingredient.
- Create lot.
- Reject negative values.
- Reject remaining > initial.
- Audit entries.

### Non-goals

- No StockMovement yet.
- No frontend yet.
- No production.

### Acceptance criteria

- Компоненты и партии сохраняются.
- Срок годности партии хранится.
- Цена партии хранится.
- AuditLog работает.

---

## PR6 — Packaging and StockMovement backend

### Goal

Добавить тару и универсальный журнал складских движений.

### Models

```text
PackagingItem
StockMovement
```

### PackagingItem fields

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
```

### StockMovement fields

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
```

### API

```text
GET /api/packaging
POST /api/packaging
GET /api/packaging/{id}
PATCH /api/packaging/{id}
POST /api/packaging/{id}/archive

GET /api/stock-movements
POST /api/stock-movements
```

### Rules

- All stock changes through movement.
- Outbound cannot make stock negative.
- Manual correction requires reason.
- Movement writes AuditLog.

### Tests

- Create packaging.
- Inbound packaging.
- Outbound packaging.
- Ingredient lot movement.
- Reject insufficient stock.
- Audit movement.

### Non-goals

- No automatic production write-off.
- No alerts.

### Acceptance criteria

- Тара учитывается.
- Остатки изменяются через движения.
- История склада прозрачна.

---

## PR7 — Inventory UI

### Goal

Сделать UI для компонентов, партий, тары и движений.

### Frontend pages

```text
/stock
/stock/ingredients
/stock/ingredients/:id
/stock/lots
/packaging
/stock/movements
```

### UI

- ingredient list;
- search;
- filters;
- ingredient card;
- lots tab;
- movements tab;
- add inbound;
- manual adjustment;
- packaging list/card;
- status badges:
  - нормально;
  - мало;
  - скоро истечет;
  - истекло.

### Backend support

Optional summary endpoint:

```text
GET /api/stock/summary
```

### Tests

- Frontend build.
- Manual create ingredient/lot/packaging.
- Manual stock movement.

### Non-goals

- No alert engine.
- No purchase suggestions.

### Acceptance criteria

- Пользователь может вести компоненты.
- Пользователь может вести партии.
- Пользователь может вести тару.
- Остатки видны в UI.

---

# PHASE 4 — Recipe core

## PR8 — Recipe backend models

### Goal

Создать базовые рецепты, версии и строки рецепта.

### Models

```text
RecipeTemplate
RecipeVersion
RecipeIngredient
```

### API

```text
GET /api/recipes
POST /api/recipes
GET /api/recipes/{id}
PATCH /api/recipes/{id}
POST /api/recipes/{id}/archive

POST /api/recipes/{id}/versions
GET /api/recipe-versions/{id}
PATCH /api/recipe-versions/{id}

POST /api/recipe-versions/{id}/ingredients
PATCH /api/recipe-ingredients/{id}
DELETE /api/recipe-ingredients/{id}
```

### Rules

- Significant formula change creates a new version.
- Historical versions are not silently overwritten.
- RecipeIngredient percent uses Decimal.
- Ingredient row deletion is audited.

### Tests

- Create recipe.
- Create version.
- Add ingredient row.
- Archive recipe.
- Audit entries.

### Non-goals

- No calculation service yet.
- No client recipes yet.

### Acceptance criteria

- Рецепты структурированы.
- Версии работают.
- Строки рецепта связаны с компонентами.

---

## PR9 — Recipe calculation service

### Goal

Рассчитывать граммы, проверять проценты, считать стоимость, обрабатывать плотность.

### Service

```text
RecipeCalculationService
DensityConversionService
CostCalculationService
```

### API

```text
POST /api/recipe-versions/{id}/calculate
```

### Calculation rules

```text
required_grams = final_batch_grams * percent / 100
grams = ml * density
```

### Response includes

- final batch grams;
- total percent;
- valid/invalid total;
- required grams per ingredient;
- density warnings;
- estimated cost;
- recipe warnings.

### Tests

- 5% of 153g = 7.65g.
- Total 100 valid.
- Below/above 100 invalid.
- ml to grams with density.
- missing density warning.
- estimated cost.

### Non-goals

- No stock write-off.
- No FEFO selection.

### Acceptance criteria

- Расчеты работают через Decimal.
- Пользователь видит warnings.
- Нет скрытой нормализации рецепта.

---

## PR10 — Recipe UI

### Goal

Сделать удобный UI рецептов и калькулятора.

### Pages

```text
/recipes
/recipes/:id
/recipe-versions/:id
```

### UI

- recipe list;
- filters;
- recipe card;
- versions tab;
- ingredients table;
- phases;
- percent total;
- batch size calculator;
- gram output;
- density warnings;
- estimated cost;
- create new version.

### UX

Всегда показывать:

```text
Сумма рецепта: 100% / меньше 100% / больше 100%
Итоговый объем: ...
Себестоимость: ...
Предупреждения: ...
```

### Tests

- Build.
- Manual create recipe.
- Manual calculate.

### Non-goals

- No client recipes.
- No PDF.

### Acceptance criteria

- Пользователь может создать рецепт.
- Пользователь может пересчитать рецепт.
- Пользователь видит себестоимость и предупреждения.

---

# PHASE 5 — Clients, individual formulas, wishes and feedback

## PR11 — Clients

### Goal

Создать карточку клиента как будущий рабочий центр.

### Model

```text
Client
```

### Fields

```text
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
```

### API

```text
GET /api/clients
POST /api/clients
GET /api/clients/{id}
PATCH /api/clients/{id}
POST /api/clients/{id}/archive
```

### Frontend

```text
/clients
/clients/:id
```

Карточка клиента с вкладками-заглушками:

```text
Профиль
Заказы
Индивидуальные рецепты
Пожелания
Обратная связь
История
Файлы
```

### Privacy

Не писать чувствительные заметки полностью в AuditLog.

### Tests

- Create/update/archive client.
- Audit without full sensitive notes.
- UI build.

### Non-goals

- No client recipes yet.
- No orders yet.

### Acceptance criteria

- Клиента можно создать и редактировать.
- Карточка клиента понятна.
- Клиентская информация не утекает в технический лог.

---

## PR12 — Client recipes

### Goal

Создать индивидуальные рецепты, привязанные к клиентам.

### Models

```text
ClientRecipe
ClientRecipeIngredient
```

### API

```text
GET /api/client-recipes
POST /api/client-recipes/from-recipe-version
GET /api/client-recipes/{id}
PATCH /api/client-recipes/{id}
POST /api/client-recipes/{id}/archive
POST /api/client-recipes/{id}/calculate
```

### Rules

- Create from RecipeVersion by copying rows.
- Editing ClientRecipe does not mutate base recipe.
- ClientRecipe calculates with same calculation service.
- ClientRecipe visible in client card.

### Frontend

- Client card tab “Индивидуальные рецепты”.
- Button “Создать из базового рецепта”.
- ClientRecipe detail page.
- Reason for individualization.

### Tests

- Create from base version.
- Base version unchanged.
- Calculation works.
- Audit log.

### Non-goals

- No wishes/feedback yet.
- No orders.

### Acceptance criteria

- У клиента есть индивидуальный рецепт.
- Он связан с исходной формулой.
- Его можно считать отдельно.

---

## PR12b — Client wishes and feedback layer

### Goal

Добавить слой пожеланий и обратной связи клиента, чтобы вести индивидуальный подход.

### Models

```text
ClientWish
ClientFeedback
```

### ClientWish fields

```text
client_id
related_order_id
related_client_recipe_id
text
importance
status
notes
created_at
resolved_at
```

Statuses:

```text
new
considered
applied
rejected
postponed
archived
```

### ClientFeedback fields

```text
client_id
order_id
client_recipe_id
reaction_notes
liked
disliked
what_to_change_next_time
created_at
```

### API

```text
GET /api/clients/{id}/wishes
POST /api/clients/{id}/wishes
PATCH /api/client-wishes/{id}

GET /api/clients/{id}/feedback
POST /api/clients/{id}/feedback
PATCH /api/client-feedback/{id}
```

### Frontend

Client card tabs:

```text
Пожелания
Обратная связь
```

Actions:

- add wish;
- mark as applied/postponed/rejected;
- link wish to recipe/order;
- add feedback after order;
- create new client recipe from wish/feedback, if available.

### Tests

- Create wish.
- Change wish status.
- Create feedback.
- Link feedback to order/client recipe.
- Audit logs without leaking sensitive text unnecessarily.

### Non-goals

- No automatic AI recommendations.
- No medical advice.

### Acceptance criteria

- Можно вести пожелания клиента.
- Можно вести обратную связь.
- Можно связать пожелание с рецептом/заказом.
- История индивидуального подхода становится видимой.

---

# PHASE 6 — Orders

## PR13 — Orders backend

### Goal

Создать заказ как центральный объект работы.

### Model

```text
Order
```

### Fields

```text
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
```

### Statuses

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

### API

```text
GET /api/orders
POST /api/orders
GET /api/orders/{id}
PATCH /api/orders/{id}
POST /api/orders/{id}/status
POST /api/orders/{id}/cancel
```

### Rules

- Order must reference RecipeVersion or ClientRecipe.
- Status changes explicit.
- Order linked to Client.

### Tests

- Create order with RecipeVersion.
- Create order with ClientRecipe.
- Reject order without recipe.
- Status transition.
- AuditLog.

### Non-goals

- No production readiness yet.
- No write-off.

### Acceptance criteria

- Заказ создается.
- Заказ связан с клиентом и рецептом.
- Статусы работают.

---

## PR14 — Orders UI

### Goal

Сделать UI для заказов.

### Pages

```text
/orders
/orders/:id
```

### UI

- order list;
- status filters;
- client search;
- order card;
- choose client;
- choose recipe or client recipe;
- target grams;
- packaging;
- sale price;
- notes;
- status buttons.

### Client card

- Orders tab shows client orders.

### Tests

- Build.
- Manual create order.

### Non-goals

- No production confirmation.
- No automatic stock write-off.

### Acceptance criteria

- Пользователь может создать заказ.
- Заказ виден в карточке клиента.
- UI показывает следующий шаг.

---

# PHASE 7 — Production

## PR15 — Production readiness service

### Goal

Проверять, можно ли изготовить заказ.

### Service

```text
ProductionReadinessService
LotSelectionService
```

### API

```text
POST /api/orders/{id}/check-production-readiness
```

### Checks

- recipe exists;
- total percent;
- required grams;
- density warnings;
- ingredient lots availability;
- expiration;
- packaging availability;
- estimated cost;
- tax;
- margin.

### FEFO

```text
First Expired, First Out
```

### Tests

- Enough stock.
- Missing ingredient.
- Missing packaging.
- Expired lot.
- FEFO selection.
- Missing density warning.
- Cost/tax/margin estimate.

### Non-goals

- No write-off.
- No ProductionBatch creation.

### Acceptance criteria

- Система объясняет, можно ли изготовить заказ.
- Ничего не списывает без подтверждения.
- Blocking issues and warnings are structured.

---

## PR16 — ProductionBatch and confirmed write-off

### Goal

Реализовать фактическое производство и автоматическое списание.

### Models

```text
ProductionBatch
ProductionBatchIngredient
ProductionBatchPackaging
```

### API

```text
POST /api/orders/{id}/produce
```

### Flow

```text
readiness check
→ confirmation
→ transaction
→ create ProductionBatch
→ create StockMovements
→ update lots/packaging
→ update order status
→ AuditLog
→ commit
```

### Rules

- Transactional.
- Cannot produce same order twice.
- Historical snapshot preserved.
- No partial write-off.

### Tests

- Production creates batch.
- Ingredient lots reduced.
- Packaging reduced.
- Order status produced.
- Cannot produce twice.
- Rollback on failure.
- Audit logs.

### Non-goals

- No PDF.
- No labels.

### Acceptance criteria

- Заказ можно произвести.
- Остатки списываются.
- Производственная партия сохраняется.
- История прозрачна.

---

## PR17 — Production UI

### Goal

Сделать UI проверки и подтверждения производства.

### UI

In order card:

- “Проверить изготовление”.
- Required ingredients.
- Selected lots.
- Packaging.
- Warnings.
- Cost/tax/margin.
- “Изготовить”.
- Confirmation dialog.

### UX

Before production show:

```text
Что будет списано
Какие партии будут использованы
Есть ли предупреждения
Сколько себестоимость
Сколько маржа
```

### Tests

- Build.
- Manual full production flow.

### Non-goals

- No purchase list generation yet.

### Acceptance criteria

- Пользователь понимает, что будет списано.
- Нельзя случайно произвести заказ.
- После производства UI показывает результат.

---

# PHASE 8 — Alerts, purchases and dashboard

## PR18 — Alert engine

### Goal

Создать систему алертов.

### Model

```text
Alert
```

### Types

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

### API

```text
GET /api/alerts
POST /api/alerts/regenerate
POST /api/alerts/{id}/resolve
POST /api/alerts/{id}/dismiss
```

### Rules

- Idempotent/deduplicated.
- Human-readable message.
- Recommended action.
- Severity.

### Tests

- Low stock.
- Expiration.
- Missing density.
- Recipe total invalid.
- Deduplication.
- Resolve/dismiss.

### Non-goals

- No external notifications.

### Acceptance criteria

- Алерты появляются.
- Алерты понятны.
- Алерты можно закрыть/решить.

---

## PR19 — PurchaseSuggestion engine

### Goal

Автоматически формировать закупочный список.

### Model

```text
PurchaseSuggestion
```

### Reasons

```text
below_minimum_stock
insufficient_for_order
predicted_shortage
expiration_replacement
manual
```

### API

```text
GET /api/purchase-suggestions
POST /api/purchase-suggestions/regenerate
POST /api/purchase-suggestions
PATCH /api/purchase-suggestions/{id}
POST /api/purchase-suggestions/{id}/mark-purchased
POST /api/purchase-suggestions/{id}/dismiss
```

### Forecast MVP

- average usage over last 30/60/90 days;
- estimate days remaining;
- suggest purchase if below threshold.

### Tests

- Below minimum creates suggestion.
- Insufficient for order creates suggestion.
- Manual suggestion.
- Mark purchased.
- Duplicate avoidance.

### Non-goals

- No supplier integration.
- No online ordering.

### Acceptance criteria

- Закупочный список формируется.
- У каждой позиции есть причина.
- Пользователь может отметить покупку.

---

## PR20 — Dashboard

### Goal

Сделать главный экран ежедневной работы.

### Backend

Optional:

```text
GET /api/dashboard
```

### Frontend blocks

- onboarding checklist;
- active orders;
- orders waiting for materials;
- alerts;
- purchase suggestions;
- quick actions;
- backup reminder.

### Dashboard answers

```text
Что сделать сегодня?
Какие заказы ждут?
Что можно изготовить?
Чего не хватает?
Что скоро испортится?
Что купить?
```

### Tests

- Dashboard endpoint.
- Build.

### Non-goals

- No advanced charts.

### Acceptance criteria

- После открытия системы пользователь понимает текущую ситуацию.
- Dashboard не перегружен.
- Есть быстрые действия.

---

# ONBOARDING LINE 2 — Usage learning

## O3 — Guided setup checklist

### Goal

Помочь пользователю пройти первые шаги.

### Scope

Checklist steps:

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

### UI

- Dashboard checklist.
- Auto-complete steps.
- Hide checklist.
- Restore checklist.

### Tests

- Step completion detected.
- Checklist hidden/restored.

### Non-goals

- No complex interactive tour.

### Acceptance criteria

- Пользователь видит первые шаги.
- Шаги отмечаются автоматически.
- Checklist не мешает после завершения.

---

## O4 — Demo data mode

### Goal

Дать безопасный режим обучения.

### Scope

Create demo data:

- demo client;
- demo ingredients;
- demo lots;
- demo packaging;
- demo recipe;
- demo client recipe;
- demo order.

Rules:

- demo data clearly marked;
- demo data removable;
- deleting demo data does not affect real data.

### Tests

- Create demo data.
- Delete demo data.
- Real data unaffected.

### Non-goals

- No fake production mixed with real history unless clearly marked.

### Acceptance criteria

- Можно потренироваться.
- Демо легко удалить.
- Демо не портит реальную базу.

---

## O5 — In-app help center

### Goal

Добавить офлайн-справку внутри приложения.

### Content

```text
Как создать рецепт
Как добавить компонент
Как добавить партию
Как создать клиента
Как создать индивидуальный рецепт
Как создать заказ
Как изготовить заказ
Как сделать backup
Что такое плотность
Что такое партия
Что такое индивидуальный рецепт
```

### Implementation

- Markdown help files or DB records.
- `/help`
- links from relevant screens.

### Tests

- Help pages load.
- Build.

### Non-goals

- No video tutorials.
- No AI helper.

### Acceptance criteria

- Пользователь может найти помощь внутри приложения.
- Справка работает офлайн.
- Тексты простые.

---

# PHASE 9 — Import/export

## PR21 — CSV/XLSX import backend

### Goal

Создать безопасный импорт.

### Models

```text
ImportSource
ImportDraft
```

### Supported MVP

- CSV;
- XLSX.

### Target entities

- clients;
- ingredients;
- ingredient lots;
- packaging;
- stock balances;
- recipe templates basic.

### API

```text
POST /api/imports
GET /api/imports
GET /api/imports/{id}
POST /api/imports/{id}/map-columns
POST /api/imports/{id}/validate
POST /api/imports/{id}/apply
POST /api/imports/{id}/cancel
```

### Validation errors

Must include:

```text
row
column
value
expected_format
human_message
```

### Tests

- Parse CSV.
- Parse XLSX.
- Validate clients.
- Validate ingredients.
- Reject invalid numbers.
- Apply only after confirmation.
- Audit apply.

### Non-goals

- No OCR.
- No PDF/image import.

### Acceptance criteria

- Импорт идет через черновик.
- Ошибки понятны.
- Данные не применяются без подтверждения.

---

## PR22 — Import UI wizard

### Goal

Сделать пошаговый импорт.

### Steps

```text
1. Upload file
2. Choose data type
3. Map columns
4. Preview
5. Fix/see errors
6. Confirm apply
7. Result summary
```

### UX

Example error:

```text
В строке 7 в колонке “Остаток” указано “много”.
Нужно число, например 30 или 30,5.
```

### Tests

- Build.
- Manual valid import.
- Manual invalid import.

### Non-goals

- No OCR.
- No image upload.

### Acceptance criteria

- Пользователь может импортировать Excel/CSV.
- Импорт не требует разработчика.
- Ошибки объясняются человечески.

---

## PR23 — Export and restore foundation

### Goal

Дать пользователю контроль над данными.

### Scope

Exports:

```text
full JSON backup/export
clients CSV
ingredients CSV
orders CSV
stock CSV
```

Optional restore:

```text
POST /api/restore
```

Если restore рискован, честно отложить и описать ручное восстановление.

### Frontend

Settings → Data:

- export full;
- export clients;
- export ingredients;
- export orders;
- restore backup if implemented.

### Tests

- Export creates file.
- CSV valid.
- Audit export.

### Non-goals

- No cloud backup.

### Acceptance criteria

- Пользователь может выгрузить данные.
- Backup/export понятен.
- Restore либо безопасен, либо явно deferred.

---

# PHASE 10 — Reports and PDF

## PR24 — Basic reports

### Goal

Добавить базовые отчеты.

### Reports

```text
current stock
low stock
expiring lots
expired lots
orders by period
production batches by period
cost/margin by order
ingredient usage by period
client order history
```

### API

```text
GET /api/reports/stock
GET /api/reports/low-stock
GET /api/reports/expiration
GET /api/reports/orders
GET /api/reports/production
GET /api/reports/margins
GET /api/reports/ingredient-usage
```

### Frontend

```text
/reports
```

- tables;
- date filters;
- simple export if easy.

### Tests

- Report query tests.
- Build.

### Non-goals

- No advanced analytics dashboard.
- No AI insights.

### Acceptance criteria

- Пользователь видит остатки, сроки, заказы, себестоимость.
- Отчеты помогают работать без Excel.

---

## PR25 — Simple PDF export

### Goal

Добавить простые PDF.

### PDF types

```text
recipe PDF
order PDF
production batch PDF
purchase list PDF
```

### API

```text
GET /api/recipes/{id}/pdf
GET /api/orders/{id}/pdf
GET /api/production-batches/{id}/pdf
GET /api/purchase-suggestions/pdf
```

### PDF content

Recipe:

- title;
- version;
- ingredients;
- percentages;
- grams for selected size;
- technology notes;
- warnings.

Order:

- client;
- product;
- recipe;
- target grams;
- price/cost/margin optional.

Production batch:

- date;
- consumed lots;
- packaging;
- cost snapshot.

Purchase list:

- what to buy;
- why;
- recommended quantity.

### Tests

- PDF endpoint returns file.
- PDF includes key text.

### Non-goals

- No branded design.
- No labels.
- No legal certificates.

### Acceptance criteria

- Простая PDF-выгрузка работает.
- Документы читаемые.
- PDF не раздувает scope.

---

# PHASE 11 — Settings, audit and product management

## PR26 — Settings UI and user-controlled dictionaries

### Goal

Сделать систему настраиваемой без разработчика.

### Settings

- tax rate;
- expiration alert days;
- low stock thresholds;
- recipe categories;
- ingredient categories;
- ingredient roles;
- recipe phases;
- packaging categories;
- backup reminder;
- data folder path display;
- PDF basic settings.

### API

Extend settings endpoints as needed.

### Tests

- Settings update.
- Audit settings changes.
- Build.

### Non-goals

- No multi-user roles.
- No cloud settings.

### Acceptance criteria

- Пользователь может менять основные настройки.
- Новая категория не требует разработчика.
- Настройки понятны.

---

## PR27 — AuditLog viewer

### Goal

Показать историю действий.

### API

```text
GET /api/audit-logs
GET /api/audit-logs/{id}
```

Filters:

- date;
- action;
- entity_type;
- source.

### Frontend

```text
/settings/audit-log
```

UI:

- list;
- date;
- action;
- entity;
- summary;
- filters.

### Privacy

Не показывать лишние чувствительные данные.

### Tests

- Audit query.
- Build.

### Non-goals

- No rollback from audit.

### Acceptance criteria

- Пользователь видит, что происходило.
- История понятна.
- Технических деталей минимум.

---

# DEPLOYMENT LINE 2 — Packaging and update safety

## D3 — macOS package MVP

### Goal

Собрать пользовательский пакет для Mac.

### Scope

- Build frontend.
- Build/package backend runtime.
- Include migrations.
- Include launcher.
- Create:

```text
CosmeticWorkshopOS-mac.zip
```

or simple `.app` if feasible.

### User scenario

```text
Download
→ unzip
→ open app
→ first-run wizard
→ work
```

### Tests

- Start from package.
- Data directory created.
- DB created.
- Browser opens.
- Data persists after restart.

### Non-goals

- No signing.
- No auto-update.
- No App Store.
- No mandatory .dmg.

### Acceptance criteria

- Пакет можно установить удаленно.
- Пользователю не нужны Git/Python/Node/Docker.
- Приложение работает после распаковки.

---

## D4 — Update safety

### Goal

Сделать обновления безопасными.

### Scope

- App version.
- Schema version.
- Migration check at startup.
- Auto-backup before migration.
- UpdateLog.
- User-facing update status.
- Failure path with restore instruction.

### Tests

- Migration from previous schema.
- Auto-backup created before migration.
- Failed migration does not destroy DB.
- UpdateLog written.

### Non-goals

- No auto-update download.
- No signed installer.

### Acceptance criteria

- Новая версия не затирает данные.
- Перед миграцией создается backup.
- Ошибка обновления понятна.

---

## D5 — Remote install checklist

### Goal

Сделать удаленную установку повторяемой.

### Docs

```text
docs/user-install.md
docs/remote-install-checklist.md
docs/update-guide.md
docs/backup-and-restore.md
```

### Checklist

```text
1. Скачать архив
2. Распаковать
3. Запустить приложение
4. Разрешить запуск в macOS, если нужно
5. Пройти first-run wizard
6. Проверить папку данных
7. Создать backup
8. Создать тестового клиента
9. Создать тестовый компонент
10. Создать тестовый рецепт
11. Проверить перезапуск
```

### Tests

- Follow checklist on a clean Mac or clean user profile if possible.
- Document limitations.

### Non-goals

- No paid remote management tools integration.
- No auto-update.

### Acceptance criteria

- Установку можно провести удаленно.
- Другой человек может повторить по инструкции.
- После установки есть smoke-test.

---

# PHASE 12 — MVP release preparation

## PR28 — Demo data, user guide and smoke checklist

### Goal

Подготовить MVP к реальному использованию.

### Scope

- Demo seed data if not fully completed in O4.
- User guide.
- MVP smoke checklist.
- Product walkthrough.

### Docs

```text
docs/user-guide.md
docs/mvp-smoke-checklist.md
```

### Smoke checklist

```text
Create ingredient
Create lot
Create packaging
Create recipe
Calculate recipe
Create client
Create client recipe
Create wish
Create order
Check production readiness
Produce order
See stock update
See alert
See purchase suggestion
Create backup
Export data
Restart app
```

### Tests

- App starts with demo data.
- Manual smoke documented.

### Non-goals

- No new major features.

### Acceptance criteria

- Новый пользователь может пройти основной сценарий.
- Технический специалист может проверить MVP.
- Документация актуальна.

---

## PR29 — MVP hardening

### Goal

Закрыть blockers и довести систему до usable MVP.

### Scope

- Fix critical bugs.
- Improve validation.
- Improve empty states.
- Improve onboarding.
- Ensure audit coverage.
- Ensure backup works.
- Ensure migration safety.
- Ensure production transaction.
- Ensure import preview.
- Ensure no raw stack traces.
- Ensure UI labels are human-readable.
- Update docs.

### Required checks

- backend tests;
- frontend build;
- migration from empty DB;
- backup smoke;
- import smoke;
- production smoke;
- package smoke;
- restart persistence check.

### Non-goals

- No big new functionality unless required for MVP acceptance.

### Acceptance criteria

MVP is ready when user can:

```text
1. Open local app
2. Complete first-run wizard
3. Create first backup
4. Create ingredient
5. Create ingredient lot with expiration date
6. Create packaging
7. Create base recipe
8. Create recipe version
9. Calculate grams from percent
10. See density warning if needed
11. Create client
12. Create client recipe
13. Add client wish/feedback
14. Create order
15. Check production readiness
16. Confirm production
17. See automatic stock write-off
18. See updated stock
19. See alerts
20. See purchase suggestions
21. Import CSV/XLSX through preview
22. Export data
23. View audit history
24. Restart app without data loss
25. Use system without developer for daily tasks
```

---

# V2+ — Future roadmap

Эти этапы не входят в MVP, но архитектура должна их не блокировать.

## V2.1 — Attachments UI

### Scope

- Attach files to clients, recipes, orders, ingredients.
- Store metadata.
- Local file storage.
- UI for upload/download.

### Non-goals

- OCR.

---

## V2.2 — OCR import drafts

### Scope

- Upload PDF/image.
- OCR extraction.
- Create ImportDraft.
- Manual review.
- Apply after confirmation.

### Hard rule

OCR output is never trusted automatically.

---

## V2.3 — Cloud backup

### Scope

- Manual cloud backup.
- Restore path.
- Clear privacy warning.

### Non-goals

- Real-time sync.

---

## V2.4 — Phone read-only view

### Scope

- Responsive read-only UI.
- Clients.
- Recipes.
- Orders.
- Purchases.
- Alerts.

### Non-goals

- Native mobile app.
- Full mobile editing.

---

## V2.5 — Cloud sync

### Scope

- Sync model.
- Conflict detection.
- Cloud database.
- Sync logs.
- Manual conflict resolution.

### Note

High complexity. Requires separate architecture document.

---

## V2.6 — Certification and documents module

### Scope

- Store certificates/declarations.
- Link documents to components/products.
- Expiration alerts.

### Non-goals

- Legal advice.
- Automatic certification generation.

---

## V2.7 — Advanced analytics

### Scope

- Profit by period.
- Top products.
- Top clients.
- Ingredient usage trends.
- Purchase forecast.
- Stock turnover.

### Non-goals

- Full accounting.
- Tax filing.

---

## V2.8 — Signed installer and auto-update

### Scope

- Signed macOS app.
- DMG package.
- Update download.
- Migration-safe auto-update.

### Non-goals

- App Store unless separately required.

---

# Codex task template

Каждый PR лучше запускать в Codex таким шаблоном:

```markdown
# Task: <PR number and title>

## Context

You are working on `cosmetic-workshop-os`.

Read and follow:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/product-spec.md`
- `docs/domain-model.md`
- `docs/ui-ux-contract.md`

This PR implements only:

`<PR number and title>`

## Goal

<Explain the user value and engineering goal.>

## Scope

Implement:

- ...
- ...
- ...

## Non-goals

Do not implement:

- ...
- ...
- ...

## Architecture constraints

- Keep local-first architecture.
- Keep user data outside app/repo.
- Use backend domain services for business logic.
- Add migrations for schema changes.
- Use Decimal for recipe/cost calculations.
- Log important actions in AuditLog.
- Keep UI human-readable.
- Do not add cloud/mobile/OCR unless explicitly scoped.

## Backend requirements

- ...

## Frontend requirements

- ...

## Tests

Add/update tests for:

- ...

Run available checks and report results.

## Acceptance criteria

- ...
- ...
- ...

## PR summary required format

Use:

## Summary
## Scope
## Data model / migrations
## User-visible changes
## Tests
## Risks / limitations
## Follow-up
```

---

# Final MVP definition

MVP считается достигнутым, если система дает клиентке возможность ежедневно отвечать на вопросы:

```text
Что нужно сделать сегодня?
Для кого заказ?
По какой формуле?
Это базовый рецепт или индивидуальный?
Какие пожелания клиента надо учесть?
Сколько граммов каждого компонента взять?
Есть ли компоненты и тара?
Какие партии использовать?
Что скоро закончится?
Что скоро испортится?
Что нужно купить?
Сколько стоит производство?
Сколько будет маржа?
Что было сделано и когда?
Где лежит backup?
Как продолжить работу без помощи разработчика?
```

Если приложение отвечает на эти вопросы, запускается локально, хранит данные безопасно, обновляется через backup/migrations и имеет понятный onboarding, значит MVP можно считать рабочим.
