# cosmetic-workshop-os — Полная архитектура проекта

Проект: **cosmetic-workshop-os**  
Клиентское название: **Мастерская косметолога**  
Тип продукта: **local-first web-приложение для учета рецептур, клиентов, запасов, заказов, производства, алертов и закупок косметической мастерской**  
Документ: **docs/architecture.md**  
Версия: **0.2**  
Статус: **архитектурный контракт для реализации через Codex**

---

## 1. Назначение документа

Этот документ описывает целевую архитектуру проекта `cosmetic-workshop-os`.

Документ нужен для:

- разработки через Codex;
- фиксации архитектурных границ;
- предотвращения случайного раздувания scope;
- защиты данных пользователя;
- обеспечения будущих обновлений;
- подготовки локального деплоя на MacBook;
- создания понятного UI/UX для нетехнического пользователя;
- подготовки системы к будущему облаку, мобильному просмотру, OCR и расширенной аналитике.

Этот документ должен использоваться вместе с:

```text
AGENTS.md
README.md
docs/product-spec.md
docs/roadmap.md
docs/domain-model.md
docs/ui-ux-guidelines.md
docs/import-format.md
docs/backup-and-restore.md
docs/local-install.md
docs/update-guide.md
docs/user-guide.md
```

---

## 2. Краткое описание продукта

`cosmetic-workshop-os` — это локальная рабочая система для специалиста, который самостоятельно производит косметические продукты: кремы, сыворотки, тоники, умывашки, шампуни, мыло и другие средства.

Система должна помогать пользователю:

- хранить базовые рецепты;
- вести версии рецептов;
- создавать индивидуальные рецепты под конкретных клиентов;
- рассчитывать проценты и граммы;
- переводить мл в граммы через плотность;
- учитывать компоненты, партии компонентов, сроки годности и остатки;
- учитывать тару и расходные материалы;
- вести клиентов;
- фиксировать пожелания и обратную связь клиентов;
- создавать заказы;
- проверять возможность изготовления заказа;
- автоматически списывать компоненты и тару при производстве;
- рассчитывать себестоимость, налог, маржу и маржинальность;
- формировать алерты;
- формировать закупочный список;
- импортировать данные из Excel/CSV;
- экспортировать данные и создавать резервные копии;
- обучать пользователя работе через onboarding, подсказки, checklist и встроенную справку.

---

## 3. Главные архитектурные принципы

### 3.1. Local-first

Первая версия должна работать локально на MacBook без обязательного подключения к интернету.

Это означает:

- основная база хранится на устройстве пользователя;
- приложение запускается локально;
- интерфейс открывается в браузере;
- интернет не требуется для ежедневной работы;
- резервные копии доступны пользователю;
- в будущем можно добавить облачную копию или синхронизацию.

---

### 3.2. API-first even when local

Даже если приложение работает локально, оно должно иметь четкую backend API-архитектуру.

Нельзя делать критичную бизнес-логику только во frontend.

Правильный поток:

```text
Frontend UI
  ↓
Backend API
  ↓
Domain services
  ↓
Repositories
  ↓
Database
```

Такой подход позволит позже:

- перенести backend в облако;
- заменить SQLite на PostgreSQL;
- добавить мобильный read-only доступ;
- добавить синхронизацию;
- переиспользовать бизнес-логику без переписывания.

---

### 3.3. Код отдельно, данные отдельно

Приложение и пользовательские данные должны храниться отдельно.

Нельзя хранить SQLite-базу внутри папки репозитория, временной сборки или пакета приложения.

Правильная структура на устройстве пользователя:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
    backup-YYYY-MM-DD-HHMM.json
  exports/
  attachments/
  logs/
```

Альтернативный системный вариант:

```text
~/Library/Application Support/CosmeticWorkshopOS/
```

Для текущего пользователя предпочтительнее папка в `Documents`, потому что ее проще найти без технических знаний.

---

### 3.4. Приложение должно быть поставляемым продуктом, а не репозиторием

Пользователь не должен:

- клонировать GitHub-репозиторий;
- устанавливать Git;
- устанавливать Python;
- устанавливать Node.js;
- запускать Docker;
- открывать терминал;
- выполнять команды вручную.

Для пользователя нормальный сценарий:

```text
Скачать архив/пакет
→ распаковать
→ открыть приложение
→ пройти первый запуск
→ начать работу
```

GitHub и Codex используются для разработки, но не как пользовательский способ запуска.

---

### 3.5. Все важные действия логируются

Система должна хранить историю важных действий:

- создание/изменение клиента;
- создание/изменение рецепта;
- создание новой версии рецепта;
- создание индивидуального рецепта;
- создание заказа;
- изменение статуса заказа;
- создание производственной партии;
- списание компонентов;
- списание тары;
- добавление партии компонента;
- корректировка склада;
- импорт;
- экспорт;
- создание backup;
- изменение настроек;
- завершение onboarding;
- обновление приложения и миграция базы.

При этом чувствительные данные клиента нельзя писать в лог полностью.

---

### 3.6. Исторические данные нельзя ломать

Нельзя silently mutate исторические данные, от которых зависит производство.

Например:

- заказ должен ссылаться на конкретную версию рецепта;
- производственная партия должна хранить snapshot использованных компонентов;
- изменение рецепта после производства не должно менять старую производственную партию;
- изменение цены компонента не должно менять себестоимость старого заказа;
- изменение плотности компонента не должно переписывать уже произведенный расчет без явного действия.

---

### 3.7. Все импорты только через черновики

Импорт из Excel/CSV/PDF/images не должен сразу менять основную базу.

Обязательный поток:

```text
ImportSource
→ ImportDraft
→ column mapping
→ validation
→ preview
→ user confirmation
→ apply
→ AuditLog
```

PDF/images/OCR в будущем также должны идти только через черновик и ручное подтверждение.

---

### 3.8. UI должен быть человекопонятным

Пользователь не технический специалист.

Интерфейс должен быть:

- простым;
- предсказуемым;
- с понятными словами;
- с подсказками;
- с пустыми состояниями;
- с первым обучением;
- с guided checklist;
- с минимальным количеством технических терминов;
- с объяснением ошибок человеческим языком.

Плохо:

```text
ValidationError: invalid decimal
```

Хорошо:

```text
В поле “Остаток” нужно указать число. Например: 30 или 30,5.
```

---

## 4. Общая архитектурная схема

```text
Packaged Local App
  ↓
Local App Launcher
  - first start check
  - data directory check
  - port check
  - migration runner
  - pre-update backup
  - backend start
  - browser open
  - graceful shutdown

Frontend UI
  - dashboard
  - recipes
  - clients
  - wishes/feedback
  - orders
  - stock
  - packaging
  - purchases
  - production
  - import
  - reports
  - settings
  - onboarding
  - help center

Backend API
  - REST endpoints
  - DTO contracts
  - validation
  - error mapping

Domain Services
  - recipe calculation
  - density conversion
  - recipe versioning
  - client recipe creation
  - client wishes/feedback
  - inventory movements
  - FEFO lot selection
  - production readiness
  - production confirmation
  - cost/tax/margin calculation
  - alert generation
  - purchase suggestion generation
  - import validation
  - onboarding progress
  - backup/export
  - update safety

Repositories / Data Access
  - SQLAlchemy models
  - query layer
  - transactions

Database
  - SQLite local
  - Alembic migrations
  - schema version

User Data Directory
  - SQLite database
  - backups
  - exports
  - attachments
  - logs

Future Extensions
  - cloud backup
  - phone read-only access
  - OCR import drafts
  - cloud sync
  - advanced analytics
```

---

## 5. Компоненты системы

---

# 5.1. Packaged Local App

## Назначение

Пользовательский пакет приложения, который можно установить или распаковать на MacBook.

## В MVP

Допустимые варианты:

```text
CosmeticWorkshopOS-mac.zip
CosmeticWorkshopOS.app
```

Идеальный future-вариант:

```text
CosmeticWorkshopOS.dmg
signed macOS app
auto-update
```

## Внутри пакета

```text
app/
  launcher
  backend_runtime/
  frontend_build/
  migrations/
  default_config/
  help/
  docs/
```

Пакет не должен содержать рабочую пользовательскую базу.

---

# 5.2. Local App Launcher

## Назначение

Слой запуска приложения на устройстве пользователя.

Launcher отвечает за:

- первый запуск;
- проверку папки данных;
- создание папок;
- проверку базы;
- применение миграций;
- создание backup перед миграцией;
- запуск backend;
- открытие браузера;
- проверку порта;
- обработку ситуации “приложение уже запущено”;
- завершение backend при закрытии приложения;
- понятные сообщения об ошибках.

## Поток запуска

```text
User opens app
  ↓
Launcher starts
  ↓
Check user data directory
  ↓
Create missing folders
  ↓
Check database exists
  ↓
If first start: create database
  ↓
Check app/schema version
  ↓
If migration needed: create backup
  ↓
Run migrations
  ↓
Start backend on localhost
  ↓
Open browser
  ↓
Show UI
```

## Порт

Backend должен запускаться на локальном адресе:

```text
127.0.0.1:<configured_port>
```

Например:

```text
127.0.0.1:8765
```

Если порт занят:

- проверить, не запущена ли уже система;
- если запущена, открыть существующий интерфейс;
- если порт занят другой программой, показать понятную ошибку.

---

# 5.3. User Data Directory

## Назначение

Хранить все пользовательские данные отдельно от кода приложения.

## Рекомендуемая структура

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

## Правила

- база данных не хранится в репозитории;
- база данных не хранится внутри приложения;
- обновление приложения не должно удалять данные;
- перед миграцией создается backup;
- пользователь должен иметь понятный доступ к backup/export;
- путь к папке данных должен быть виден в настройках.

## Сущности, связанные с хранилищем

```text
AppSettings
BackupRecord
UpdateLog
Attachment
```

---

# 5.4. Frontend UI

## Назначение

Пользовательский интерфейс.

## Основные разделы

```text
Главная
Рецепты
Клиенты
Пожелания/обратная связь
Заказы
Запасы
Тара
Закупки
Производство
Импорт
Отчеты
Настройки
Помощь
```

## Принципы UI

- desktop-first;
- mobile-aware;
- простые таблицы;
- карточки сущностей;
- понятные статусы;
- пустые состояния;
- подсказки;
- confirmation dialogs;
- человекопонятные ошибки;
- минимизация технических терминов;
- каждый экран должен подсказывать следующий шаг.

## Структура frontend

Рекомендуемая структура:

```text
frontend/
  src/
    app/
      routes/
      providers/
      layout/
    pages/
      dashboard/
      recipes/
      clients/
      orders/
      stock/
      packaging/
      purchases/
      production/
      import/
      reports/
      settings/
      onboarding/
      help/
    widgets/
      dashboard-alerts/
      onboarding-checklist/
      recipe-calculator/
      order-readiness/
      stock-summary/
    features/
      create-recipe/
      calculate-recipe/
      create-client/
      create-client-recipe/
      create-order/
      confirm-production/
      import-wizard/
      create-backup/
    entities/
      recipe/
      client/
      order/
      ingredient/
      packaging/
      alert/
      purchase-suggestion/
    shared/
      api/
      ui/
      empty-states/
      tooltips/
      form-hints/
      status-badges/
      confirmation-dialogs/
      error-messages/
      utils/
```

---

# 5.5. Backend API

## Назначение

Единый API для frontend и будущих клиентов.

## Принципы

- REST endpoints;
- явные DTO;
- человекопонятные ошибки;
- backend validation;
- domain logic in services;
- no critical business logic only in frontend;
- transactional operations where needed;
- structured warnings.

## Пример модулей API

```text
backend/app/api/
  health.py
  settings.py
  onboarding.py
  clients.py
  client_wishes.py
  recipes.py
  client_recipes.py
  ingredients.py
  ingredient_lots.py
  packaging.py
  stock_movements.py
  orders.py
  production.py
  alerts.py
  purchases.py
  imports.py
  exports.py
  backups.py
  reports.py
  audit_logs.py
  help.py
```

---

# 5.6. Domain Services

## Назначение

Содержат бизнес-логику системы.

## Основные сервисы

```text
RecipeCalculationService
RecipeVersioningService
DensityConversionService
ClientRecipeService
ClientWishService
ClientFeedbackService
InventoryService
StockMovementService
LotSelectionService
ProductionReadinessService
ProductionConfirmationService
CostCalculationService
AlertGenerationService
PurchaseSuggestionService
ImportValidationService
ImportApplyService
BackupService
ExportService
MigrationSafetyService
OnboardingService
HelpContentService
AuditService
```

---

# 5.7. Repositories / Data Access

## Назначение

Изолировать работу с базой данных.

## Правила

- не размазывать SQL-запросы по API routes;
- domain services используют repositories;
- транзакции для производства и импорта;
- миграции через Alembic;
- Decimal для расчетов.

---

# 5.8. Database

## MVP

```text
SQLite
```

## Future

```text
PostgreSQL
```

## Правила

- все schema changes через миграции;
- нельзя silently drop business data;
- schema version хранится в базе;
- перед миграцией создается backup;
- тестировать migration from empty DB;
- тестировать migration from previous version.

---

## 6. Основные доменные сущности

---

# 6.1. Client

Клиент косметолога.

## Поля

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
```

## Связи

```text
Client → Orders
Client → ClientRecipes
Client → ClientWishes
Client → ClientFeedback
Client → Attachments
```

## Правила

- чувствительные заметки не писать полностью в AuditLog;
- удаление заменять архивированием;
- карточка клиента должна быть рабочим центром клиента.

---

# 6.2. ClientWish

Пожелание клиента.

## Назначение

Фиксировать запросы клиента, которые могут влиять на будущие рецепты и заказы.

## Поля

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
resolved_at
```

## Статусы

```text
new
considered
applied
rejected
postponed
archived
```

## Пример

```text
Клиент попросил сделать крем менее жирным.
Пожелание связано с индивидуальным рецептом.
На основе пожелания создается новая версия рецепта.
```

---

# 6.3. ClientFeedback

Обратная связь клиента.

## Назначение

Фиксировать результат использования продукта.

## Поля

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
```

## Правила

- feedback может приводить к созданию ClientWish;
- feedback может приводить к новой версии индивидуального рецепта;
- feedback должен быть виден из карточки клиента и заказа.

---

# 6.4. RecipeTemplate

Базовый рецепт.

## Поля

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
```

## Правила

- не привязан к одному клиенту;
- значимые изменения идут через RecipeVersion;
- не удалять, архивировать.

---

# 6.5. RecipeVersion

Конкретная версия базового рецепта.

## Поля

```text
id
recipe_template_id
version_number
status
change_reason
notes
created_at
updated_at
```

## Связи

```text
RecipeVersion → RecipeIngredients
RecipeVersion → Orders
RecipeVersion → ProductionBatches
RecipeVersion → ClientRecipes
```

## Правила

- заказ должен ссылаться на конкретную версию;
- производство должно хранить snapshot расчета;
- историческую версию нельзя silently rewrite.

---

# 6.6. ClientRecipe

Индивидуальный рецепт клиента.

## Поля

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
```

## Связи

```text
ClientRecipe → ClientRecipeIngredients
ClientRecipe → Orders
ClientRecipe → ClientWishes
ClientRecipe → ClientFeedback
```

## Правила

- индивидуальный рецепт является first-class recipe;
- изменения индивидуального рецепта не меняют базовый рецепт;
- желательно поддерживать версии индивидуального рецепта или историю изменений.

---

# 6.7. RecipeIngredient / ClientRecipeIngredient

Строка рецепта.

## Поля

```text
id
recipe_version_id or client_recipe_id
ingredient_id
phase
percent
input_unit
sort_order
notes
```

## Правила

- проценты хранятся через Decimal;
- сумма рецепта проверяется;
- система не нормализует проценты без явного действия пользователя.

---

# 6.8. Ingredient

Компонент.

## Поля

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

## Правила

- базовая расчетная единица рецептов - граммы;
- мл переводятся в граммы через density;
- если density отсутствует, показывать warning;
- не удалять используемый компонент, архивировать.

---

# 6.9. IngredientLot

Партия компонента.

## Поля

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

## Правила

- остаток партии не может быть отрицательным;
- remaining_quantity не может быть больше initial_quantity;
- списание по умолчанию FEFO;
- партии нужны для сроков годности и себестоимости.

---

# 6.10. PackagingItem

Тара или расходный материал.

## Поля

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

---

# 6.11. StockMovement

Движение склада.

## Поля

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

## Типы

```text
inbound
outbound
manual_adjustment
expiration_writeoff
production_usage
reversal
correction
```

## Правила

- все изменения остатков через movement;
- ручная корректировка должна иметь reason;
- производственное списание должно ссылаться на ProductionBatch;
- списание не может сделать остаток отрицательным.

---

# 6.12. Order

Заказ.

## Поля

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
```

## Статусы

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

## Правила

- заказ должен ссылаться либо на RecipeVersion, либо на ClientRecipe;
- изменение статуса логируется;
- заказ нельзя “произвести” дважды.

---

# 6.13. ProductionBatch

Производственная партия.

## Поля

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
```

> **Снапшот-поля ставки — `CR-008`, `C2-II` влит (PR #152).** `C2-II` добавил ровно два nullable поля — `tax_rate_percent_snapshot` и `tax_rate_effective_at_snapshot` — миграцией `0019_production_batch_tax_rate_snapshots`. Они **есть** на текущем `main`. Существующие `sale_price`, `total_cost`, `tax`, `margin` и `margin_percent` переиспользуются; дублирующие денежные снапшот-поля (`sale_price_snapshot`, `total_cost_snapshot`, `tax_amount_snapshot`, `margin_amount_snapshot`) **не** авторизованы. Backfill не выполняется, старые строки остаются `null`. Контракт: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

## Дополнительные таблицы

```text
ProductionBatchIngredient
ProductionBatchPackaging
```

## Правила

- создается только после явного подтверждения;
- создание production batch и списания должны быть transactional;
- хранит snapshot использованных компонентов и партий;
- не пересчитывается задним числом при изменении рецепта.

---

# 6.14. Alert

Алерт.

## Поля

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
```

## Типы

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

## Правила

- alert generation должна быть идемпотентной;
- alert должен объяснять причину;
- alert должен предлагать действие.

---

# 6.15. PurchaseSuggestion

Закупочная рекомендация.

## Поля

```text
id
item_type
item_id
recommended_quantity
reason
status
created_at
notes
```

## Причины

```text
below_minimum_stock
insufficient_for_order
predicted_shortage
expiration_replacement
manual
```

---

# 6.16. ImportSource

Загруженный файл.

## Поля

```text
id
file_name
file_type
file_path
uploaded_at
status
raw_metadata
errors
```

---

# 6.17. ImportDraft

Черновик импорта.

## Поля

```text
id
import_source_id
target_entity_type
column_mapping
parsed_rows
validation_errors
status
created_at
applied_at
```

## Правила

- нельзя применять без preview;
- нельзя применять без confirmation;
- ошибки должны быть простыми;
- import apply логируется.

---

# 6.18. AuditLog

Журнал действий.

## Поля

```text
id
action
entity_type
entity_id
summary
actor_type
created_at
```

## Источники

```text
manual
system
import
production
migration
backup
onboarding
```

> **Этот перечень источников — aspirational и НЕ реализован.** Ни один write call site не сохраняет измерение source/process: нет ни колонки, ни параметра, ни значения. Реально существует только колонка **`actor_type`**, и текущий write-словарь — это **`system`** и **`user`**.
>
> **`system` и `user` — это инициаторы, а не источники.** Они описывают, кто или что запустило действие, а не процесс происхождения. Поэтому `C3-I` отдаёт **`actor_type` / `actor_label`** и **не** отдаёт поле `source`: отображение одного в другое молча изменило бы смысл поля.
>
> Настоящее поле `source` требует, чтобы write call sites начали сохранять это измерение. Это изменение на стороне записи, и оно **отложено** до отдельно принятого продуктового решения и отдельного среза. До тех пор `manual`, `import`, `production`, `migration`, `backup` и `restore` нельзя подавать как реализуемые.
>
> **Сырой сохранённый `summary` тоже не отдаётся.** API возвращает `display_summary` — безопасное русское значение, которое backend-презентер выводит из `action`. Исторические строки не переписываются. Полный контракт: `docs/audit-log.md`.
>
> **Lifecycle boundary.** C3-I (PR #159), C3-II-A (PR #161), C3-II-B1 (PR #163), C3-II-B2 (PR #166) and C3-II-B3 (PR #167) are all `DONE — MERGED AND EXACT-HEAD VERIFIED`, and the C3 artifact-finalization hardening merged as PR #168 (final reviewed head `6c57c7f5ba851ce2124577268baeda07d19ce4ae`, merge commit `867afeb0967637d07172f88c95e02e9bc500a311`), so `C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED`. `CR-009` accepts the cross-resource contract for user-created manual backups, JSON exports and report documents: a verified artifact is authoritative; audit-finalization failure preserves it and returns truthful HTTP `201` partial success; one bounded `artifact_audit_operations` ledger prepares the operation and provides idempotent finalization/reconciliation by `operation_id`. C3-II-B1 (report documents) is `DONE — MERGED AND EXACT-HEAD VERIFIED` — final reviewed head `afd65fd2878fa02a0d4dc4963812c80644a4e787`, merge commit `ef0297e41a731f082a2a21a46b361aa9aac36cfa`: migration `0020_artifact_audit_operations` creates the ledger, report-document creation reserves and commits a `prepared` row before writing either file, and one write-serialized transaction commits the `report_document.created` AuditLog row together with the `audited` transition. Bounded reconciliation runs after migrations at normal startup and once before the next document create; there is no background retry. `CR-006` is accepted and its slice C3-II-B2 merged as PR #166, so JSON export creation is audited on merged `main`. `CR-004` is now **accepted** (`PRODUCT DEFECT — BACKUP CONSISTENCY`, `HIGH`): the raw `shutil.copy2` of the live main database file silently omitted all committed-but-uncheckpointed WAL data while returning `quick_check = ok`, and produced mixed transaction state including never-committed rows. Backups now use the SQLite Online Backup API with bounded busy behaviour, and a manual backup carries its own `prepared` ledger row inside the snapshot so it can prove which operation created it. C3-II-B3 merged as PR #167, so manual backup creation is audited on merged `main`. The PR #168 hardening then made artifact verification and AuditLog persistence separate typed results for report documents and JSON exports as well: `recorded` and `audit_pending` may produce HTTP `201`, while `artifact_invalid` produces a fixed structured HTTP `500` and leaves the artifact undeleted, unaudited, unresolved and counted for bounded reconciliation, exposing no filename, path, reason, operation ID, schema version, entity count, verifier detail or SQLite detail. Full decisions: `docs/decisions/0013-file-backed-artifact-audit-semantics.md`, `docs/decisions/0014-json-export-create-confirmation-semantics.md` and `docs/decisions/0015-sqlite-backup-consistency-and-manual-audit.md`.

## File-backed artifact audit boundary

The CR-009 ledger is owned only by manual backup, JSON export and
report-document create operations. It is not a generic outbox, event bus, job
queue or workflow engine.

As of C3-II-B1 only the report-document operation has a runtime writer. The
`json_export` and `manual_backup` kinds exist in the table's `CHECK` vocabulary
so that B2 and B3 need no second migration, but no code writes them.

```text
validate/canonicalize
→ reserve safe relative artifact identity
→ commit prepared ledger row
→ create and verify artifact outside SQLite
→ insert AuditLog + mark audited in one SQLite transaction
```

Allowed ledger statuses are `prepared`, `pending_audit`, `audited` and
`abandoned`. The stable unique identity is `operation_id`; an audited operation
stores `audit_log_id`. `operation_id` is an opaque backend-generated canonical
lowercase UUID, never user-supplied or exposed by the Journal API. B1 creates
only `artifact_kind = report_document` and
`audit_action = report_document.created`; `json_export` and `manual_backup`
remain reserved.

The B1 table has the exact conceptual columns and constraints recorded in ADR
0013: typed non-null identity/kind/filename/status/action/timestamps, nullable
companion filename and nullable `audit_log_id` referencing `audit_logs.id`,
plus a status `CHECK`. Safe filename validation runs on write and
reconciliation read and rejects empty names, absolute paths, separators, `..`,
NUL and control characters. Only one active operation may own an exact
`(artifact_kind, primary_filename)` identity; active means `prepared` or
`pending_audit`.

`primary_filename` and nullable `companion_filename` are internal safe relative
filenames required for deterministic reconciliation. Report-document
filenames contain no request reason. Future B2/B3 primary filenames may contain
the canonical filename-derived reason segment accepted by CR-005; there is no
separate reason column and no raw human/request/export-manifest reason or other
separate user-authored text. CR-005 is not reopened. Ledger filenames are
never copied into AuditLog or exposed by `GET /api/audit-logs`.

Reconciliation runs after successful initialization and migrations, before
the ordinary UI is served, and once before another scoped create. It uses only
the recorded safe filenames under the expected artifact directory and shares
the idempotent finalizer. GET/list/status endpoints never reconcile. A failure
to finalize one pending event leaves it unresolved and does not make startup or
an older artifact fail; it does not hide an independent initialization or
migration failure, loop, or retry without bound.

For B1, `AuditLogRepository.create_log(...)` compatibly returns the inserted
row ID while preserving its parameters and optional caller connection.
Existing callers may ignore it. The finalizer uses that repository on one
caller-owned connection under `BEGIN IMMEDIATE` or an explicitly tested
architecture-equivalent SQLite write lock, reads status, returns an existing
audited ID, inserts only for `prepared`/`pending_audit`, then stores the new ID
and marks the ledger audited in the same transaction. Insert and ledger update
commit together or neither; no second insertion API, connection or generic
transaction framework is authorized.

The ledger stores no artifact content, Workshop profile or client data.
AuditLog stores no path, filename, reason, content, entity count, request or
response payload. Existing artifacts are not backfilled, renamed or rewritten.
The automatic `before_migration` backup remains outside CR-009 and before
migrations, so it never depends on a ledger table that may not exist yet.

---

# 6.19. OnboardingState

Прогресс первого обучения.

## Поля

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

## Шаги checklist

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

---

# 6.20. HelpArticle

Статья справки.

Может храниться как Markdown-файл или запись в БД.

## Поля

```text
slug
title
body
related_screen
order
```

## Примеры

```text
how-to-create-recipe
how-to-add-ingredient
how-to-add-lot
how-to-create-client
how-to-create-order
how-to-produce-order
how-to-create-backup
what-is-density
what-is-ingredient-lot
what-is-client-recipe
```

---

# 6.21. BackupRecord

Информация о backup.

## Поля

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

---

# 6.22. UpdateLog

Лог обновления приложения/базы.

## Поля

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

---

# 6.23. Attachment

Вложение.

## Поля

```text
id
entity_type
entity_id
file_name
file_type
file_path
created_at
notes
```

## MVP

Модель можно заложить, но полноценный UI вложений можно вынести в v2.

---

## 7. Ключевые бизнес-потоки

---

# 7.1. Первый запуск

```text
User opens app
  ↓
Launcher checks user data directory
  ↓
No database found
  ↓
Create database
  ↓
Run migrations
  ↓
Open first-run wizard
  ↓
User chooses:
  - data folder
  - tax rate
  - backup reminder
  - demo data yes/no
  ↓
Create settings
  ↓
Create OnboardingState
  ↓
Open Dashboard with checklist
```

---

# 7.2. Создание базового рецепта

```text
User opens Recipes
  ↓
Create RecipeTemplate
  ↓
Create initial RecipeVersion
  ↓
Add RecipeIngredients
  ↓
Validate total percent
  ↓
Calculate for sample batch size
  ↓
Show warnings
  ↓
Save
  ↓
AuditLog
```

---

# 7.3. Создание индивидуального рецепта клиента

```text
Open Client
  ↓
Click “Создать индивидуальный рецепт”
  ↓
Choose source RecipeVersion
  ↓
System copies recipe rows
  ↓
User edits formula
  ↓
User adds reason
  ↓
Save ClientRecipe
  ↓
AuditLog
```

---

# 7.4. Пожелание клиента → новая версия рецепта

```text
Open Client
  ↓
Add ClientWish
  ↓
Link to ClientRecipe or Order
  ↓
Wish status = new
  ↓
Create updated ClientRecipe version/copy
  ↓
Wish status = applied
  ↓
AuditLog
```

---

# 7.5. Создание заказа

```text
Open Orders or Client
  ↓
Create Order
  ↓
Select client
  ↓
Select RecipeVersion or ClientRecipe
  ↓
Set target batch grams
  ↓
Select packaging
  ↓
Set sale price
  ↓
Save Order
  ↓
Status = new
  ↓
AuditLog
```

---

# 7.6. Проверка готовности производства

```text
Open Order
  ↓
Click “Проверить изготовление”
  ↓
RecipeCalculationService calculates required grams
  ↓
ProductionReadinessService checks:
  - recipe total
  - density warnings
  - ingredient lots
  - expiration dates
  - packaging
  - estimated cost
  - tax/margin
  ↓
Return:
  - can_produce
  - blocking issues
  - warnings
  - selected lots
  - cost snapshot
```

---

# 7.7. Подтверждение производства

```text
Open Order
  ↓
Read readiness result
  ↓
Click “Изготовить”
  ↓
Confirmation dialog
  ↓
Transaction starts
  ↓
Create ProductionBatch
  ↓
Create ProductionBatchIngredient rows
  ↓
Create ProductionBatchPackaging rows
  ↓
Create StockMovement for ingredients
  ↓
Create StockMovement for packaging
  ↓
Update lot/package stock
  ↓
Update Order status = produced
  ↓
AuditLog
  ↓
Transaction commits
```

Если ошибка:

```text
Rollback transaction
→ show human-readable error
→ no partial write-off
```

---

# 7.8. Алерты

```text
Trigger:
  - app start
  - stock movement
  - order created
  - production confirmed
  - manual regenerate
  ↓
AlertGenerationService checks:
  - low stock
  - expiration
  - insufficient materials
  - recipe issues
  - missing density
  - backup reminder
  ↓
Create/update/dedupe alerts
  ↓
Dashboard displays alerts
```

---

# 7.9. Закупочный список

```text
Trigger:
  - alert generation
  - order readiness
  - manual regenerate
  ↓
PurchaseSuggestionService checks:
  - below minimum stock
  - missing for order
  - predicted shortage
  - expiration replacement
  ↓
Create/update suggestions
  ↓
User marks purchased
  ↓
System guides to create inbound stock movement / lot
```

---

# 7.10. Импорт Excel/CSV

```text
User opens Import
  ↓
Upload file
  ↓
Create ImportSource
  ↓
Parse rows
  ↓
Create ImportDraft
  ↓
User maps columns
  ↓
Validate rows
  ↓
Show preview/errors
  ↓
User confirms
  ↓
Apply import in transaction
  ↓
AuditLog
```

---

# 7.11. Обновление приложения

```text
User opens new app version
  ↓
Launcher checks app/schema version
  ↓
Migration needed
  ↓
Create automatic backup
  ↓
Run migrations
  ↓
Write UpdateLog
  ↓
Open app
```

Если миграция не удалась:

```text
Stop update
Show error
Keep backup
Offer restore instructions
```

---

## 8. Расчетная архитектура

---

# 8.1. Decimal only

Для процентов, граммов и денег использовать Decimal.

Не использовать float в критичных расчетах.

---

# 8.2. Расчет граммов

```text
required_grams = final_batch_grams * percent / 100
```

---

# 8.3. Проверка суммы рецепта

```text
total_percent = sum(recipe_ingredient.percent)
```

Статусы:

```text
valid_100
below_100
above_100
```

Система не должна автоматически нормализовать рецепт без явного действия.

---

# 8.4. Перевод мл в граммы

```text
grams = ml * density
```

Если density отсутствует:

- вернуть warning;
- отметить расчет как approximate;
- не скрывать warning при производстве.

---

# 8.5. FEFO selection

При списании партий компонента по умолчанию использовать:

```text
First Expired, First Out
```

То есть сначала списывать партии с ближайшим сроком годности.

---

# 8.6. Себестоимость

```text
component_cost = sum(consumed_quantity * lot_unit_cost)
packaging_cost = sum(packaging_quantity * packaging_unit_cost)
total_cost = component_cost + packaging_cost + other_cost
tax = ROUND_MONEY(sale_price * tax_rate_percent / 100)
margin = ROUND_MONEY(sale_price - total_cost - tax)
margin_percent = ROUND_PERCENT(margin / sale_price * 100)
```

Правила налоговой части (решения `CR-007` и `CR-008`):

- `tax_rate_percent` — это **процент, а не коэффициент**;
- допустимый диапазон — `0.00`–`100.00`;
- `6.00` означает `6%`, и процент **всегда делится на `100`**;
- отсутствующая ставка делает налог и зависящую от него маржу **недоступными, а не нулевыми**;
- явно настроенный `0.00` — это реальное значение, а не «не настроено»: налог равен `0.00`;
- расчёты выполняются только в `Decimal`, без binary float на любом промежуточном шаге;
- округляется **только итоговая сумма** каждой формулы: деньги — до `0.01`, процент — до `0.01`, обе с `ROUND_HALF_UP`;
- налог **вычитается** из выручки и никогда не добавляется сверх цены продажи;
- текущие настройки **никогда** не пересчитывают исторические строки `ProductionBatch`;
- после реализации налога в C2 производство и отчёты используют **сохранённые снапшоты**, а не текущую ставку;
- действующий контракт настройки: `docs/settings.md`;
- контракт расчётов и снапшотов: `docs/decisions/0012-c2-financial-calculation-snapshots.md`;
- контракт полей снапшотов: `docs/domain-model.md`.

Правила доступности и отсутствующих значений (`CR-008`):

- маржа недоступна, если недоступна цена продажи, полная себестоимость или сумма налога; отсутствующее значение **никогда** не превращается в ноль;
- процент маржи считается только когда маржа доступна **и** цена продажи строго больше нуля;
- при нулевой цене продажи налог и маржа могут быть доступны, процент маржи — `null`, и возвращается неблокирующее предупреждение `margin_percent_unavailable_zero_sale_price`;
- маржа может быть положительной, нулевой или **отрицательной**; отрицательная маржа — это достоверная информация, её нельзя обрезать до нуля, как и отрицательный процент маржи;
- некорректно сохранённое значение ставки обрабатывается защитно: расчёт недоступен, возвращается неблокирующее предупреждение `tax_rate_invalid`, значение не приводится к нулю и запрос готовности не превращается в необработанный HTTP `500`;
- **отсутствующая строка настройки и некорректно сохранённое значение** вместе образуют `no valid configured tax-rate context`: они различимы по коду предупреждения (`tax_rate_missing` против `tax_rate_invalid`, и второй **не** дублируется первым), но дают одинаковый авторитетный контекст `tax_rate_percent = null` и `tax_rate_effective_at = null`, одинаковую недоступность налога, маржи и процента маржи и одинаково **не блокируют** физическое производство; сырое некорректное значение никогда не возвращается как авторитетная ставка и никогда не попадает в readiness DTO, в запрос подтверждения или в снапшот `ProductionBatch`;
- инвариант: **отсутствующая или некорректная налоговая настройка может сделать финансовые значения недоступными, но сама по себе не блокирует физическое производство**;
- финансовые предупреждения **неблокирующие** и используют существующий механизм предупреждений готовности и существующую структуру `ProductionReadinessIssue`; параллельная система предупреждений не создаётся;
- существующие коды `tax_rate_missing`, `sale_price_missing` и `cost_data_missing` сохраняются без переименования; `CR-008` добавляет только `margin_percent_unavailable_zero_sale_price` и `tax_rate_invalid`;
- `can_produce` определяется только рецептурой, складом, партиями, тарой, жизненным циклом заказа и существующими правилами физической безопасности производства — финансовый пробел никогда не блокирует физическое производство.

Границы срезов C2 (`CR-008`, полный контракт — `docs/implementation-plan.md` § 11):

- `C2-I` — backend-оценка в существующем ответе готовности: переиспользуются существующие поля `estimated_cost`, `estimated_tax`, `estimated_margin`, добавляются `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent` и `financial_estimate_status`; поле `estimated_total_cost` **не** вводится;
- `C2-II` — неизменяемые финансовые снапшоты внутри транзакции подтверждения производства, включая обязательные-но-nullable ключи контекста ставки `expected_tax_rate_percent` и `expected_tax_rate_effective_at` и конфликт `tax_rate_context_stale`. Пара `null/null` означает «readiness не увидел действующей налоговой ставки» и покрывает **и** отсутствующую строку, **и** некорректное сохранённое значение; пропуск ключа — это не то же самое, что явный `null/null`, и отклоняется как `422 tax_rate_context_required`. Конфликт `409 tax_rate_context_stale` возникает при переходах valid → изменённый valid, valid → missing, valid → invalid, missing → valid и invalid → valid, но **не** при missing ↔ invalid, поскольку оба состояния дают одинаковый финансовый результат;
- форматы времени в C2: хранение — `YYYY-MM-DD HH:MM:SS` (UTC, SQLite text, без `T`, `Z` и смещения); API и контекст подтверждения — `YYYY-MM-DDTHH:MM:SSZ` (UTC, без дробных секунд и произвольных смещений); неканоничная метка времени в запросе отклоняется как `422 invalid_tax_rate_context`, а API никогда не отдаёт сырое хранимое представление;
- `C2-III` — бывший **зонтик планирования**, разделённый ровно на два runtime-среза: `C2-III-A` — финансовое представление заказа и `ProductionBatch` (влит как PR #154, `DONE — MERGED AND EXACT-HEAD VERIFIED`; отчёты не затронул) и `C2-III-B` — отчёты и документы отчётов по снапшотам (влит как PR #157, merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, `DONE — MERGED AND EXACT-HEAD VERIFIED`; отчёты читают персистентные снапшоты; UI заказов и `ProductionBatch` не затронул). **C2 завершён (`COMPLETED`).**
- в течение всего C2 `frontend/src/main.ts` не превышает `6399` строк, а фронтенд не выполняет финансовых вычислений.

---

## 9. UI/UX архитектура

---

# 9.1. Главная

Dashboard должен отвечать на вопросы:

```text
Что сделать сегодня?
Какие заказы ждут?
Что можно изготовить?
Чего не хватает?
Что скоро испортится?
Что нужно купить?
Какие первые шаги еще не выполнены?
```

Блоки:

- onboarding checklist;
- active orders;
- alerts;
- purchase suggestions;
- quick actions;
- backup reminder.

---

# 9.2. Карточка клиента как рабочий центр

Карточка клиента должна содержать вкладки:

```text
Профиль
Заказы
Индивидуальные рецепты
Пожелания
Обратная связь
История
Файлы
```

Цель: по одному клиенту видеть весь контекст.

---

# 9.3. Empty states

Каждый пустой раздел должен объяснять, что делать.

Пример для рецептов:

```text
У вас пока нет рецептов.
Начните с базового рецепта, например “Крем дневной”.
[Создать рецепт]
```

Пример для запасов:

```text
Здесь будут компоненты и их остатки.
Сначала добавьте компонент, потом добавьте партию с количеством и сроком годности.
[Добавить компонент]
```

---

# 9.4. Contextual help

Сложные поля должны иметь подсказки:

- плотность;
- минимальный остаток;
- партия;
- версия рецепта;
- индивидуальный рецепт;
- срок годности;
- себестоимость;
- маржа;
- производственная партия.

---

# 9.5. Confirmation dialogs

Опасные действия требуют подтверждения:

- производство заказа;
- списание остатков;
- удаление/архивирование;
- применение импорта;
- восстановление backup;
- миграция/обновление;
- удаление demo data.

---

# 9.6. Error mapping

Backend может возвращать structured errors, но frontend должен показывать человеку понятный текст.

Пример backend:

```json
{
  "code": "INSUFFICIENT_STOCK",
  "message": "Not enough stock",
  "details": {
    "ingredient": "Масло ши",
    "required": "12.00",
    "available": "5.00"
  }
}
```

Frontend:

```text
Не хватает компонента “Масло ши”.
Нужно: 12 г.
Доступно: 5 г.
Добавьте компонент в закупочный список или внесите приход.
```

---

## 10. Onboarding architecture

---

# 10.1. First-run wizard

Шаги:

```text
1. Добро пожаловать
2. Выбор папки данных
3. Налоговая ставка
4. Напоминание о backup
5. Создать демо-данные
6. Начать работу
```

---

# 10.2. Guided checklist

Показывать на Dashboard:

```text
□ Добавить первый компонент
□ Добавить первую партию
□ Добавить тару
□ Создать первый рецепт
□ Создать клиента
□ Создать индивидуальный рецепт
□ Создать заказ
□ Изготовить заказ
□ Сделать резервную копию
```

---

# 10.3. Demo data mode

Демо-данные:

- demo client;
- demo ingredients;
- demo lots;
- demo packaging;
- demo recipe;
- demo client recipe;
- demo order.

Правила:

- demo data помечаются явно;
- demo data можно удалить;
- удаление demo data не должно затрагивать реальные данные.

---

# 10.4. Help center

Встроенная справка должна работать офлайн.

Структура:

```text
/help
/help/how-to-create-recipe
/help/how-to-add-ingredient
/help/how-to-create-order
/help/how-to-produce-order
/help/how-to-create-backup
/help/what-is-density
/help/what-is-lot
/help/what-is-client-recipe
```

---

## 11. Deployment architecture

---

# 11.1. Developer mode

Для разработки:

```bash
make setup
make dev
make test
make build
```

или:

```bash
./scripts/dev_setup.sh
./scripts/dev_start.sh
```

Developer mode может использовать:

- Python;
- Node.js;
- local virtualenv;
- npm/pnpm;
- dev server.

---

# 11.2. User mode

Для пользователя:

```text
Open app
→ first-run wizard
→ work
```

Пользовательский режим не должен требовать:

- Git;
- Python install;
- Node install;
- Docker;
- terminal commands.

---

# 11.3. Build pipeline

Рекомендуемый pipeline:

```text
GitHub repository
  ↓
Codex PRs
  ↓
merge to main
  ↓
GitHub Actions build
  ↓
release artifact
  ↓
CosmeticWorkshopOS-mac.zip / .app
  ↓
remote install
```

---

# 11.4. Packaging scripts

Репозиторий должен содержать:

```text
scripts/
  dev_setup.sh
  dev_start.sh
  build_frontend.sh
  build_backend.sh
  package_macos.sh
  start_local.sh
  create_backup.sh
  restore_backup.sh
```

> **`restore_backup.sh` is a developer/support script sketch, not the product
> Restore workflow.** `CR-010` decided that MVP Restore is **launcher-assisted**
> (§ 12.4), and a terminal command must never become the permanent workflow for
> the product user. Restore is **not implemented**.

---

# 11.5. Install docs

Документы:

```text
docs/local-install.md
docs/user-install.md
docs/remote-install-checklist.md
docs/update-guide.md
docs/backup-and-restore.md
```

---

## 12. Backup and update safety

---

# 12.1. Backup types

```text
manual_backup
auto_backup_before_migration
scheduled_reminder_backup
export_backup
```

---

# 12.2. Backup contents

Минимально:

- database;
- app settings;
- schema version;
- app version;
- created_at.

Опционально:

- attachments;
- exports;
- logs.

---

# 12.3. Auto-backup before migration

Обязательное правило:

```text
Before schema migration:
  create backup
  verify backup exists
  run migration
  write UpdateLog
```

---

# 12.4. Restore — launcher-assisted (CR-010, decided 2026-08-02)

> **Status: decided, `NOT IMPLEMENTED`.** This section describes accepted
> architecture, not shipped behaviour. Durable decision:
> `docs/decisions/0016-launcher-assisted-restore.md`; complete product contract:
> `docs/backup-and-restore.md`.
>
> ```text
> C4 — ACTIVE
> C4 product decision — COMPLETE
> C4 implementation — NOT STARTED
> CR-010 — ACCEPTED — NOT IMPLEMENTED
> C4-I — AUTHORIZED AFTER THE CR-010 DOCUMENTATION PR MERGES — NOT IMPLEMENTED
> C4-II — PLANNED — NOT AUTHORIZED
> C4-III — PLANNED — NOT AUTHORIZED
> Restore — NOT IMPLEMENTED
> ```

```text
MVP Restore is launcher-assisted.

Restore is not performed by a running FastAPI backend endpoint and is not
implemented as an ordinary SPA mutation.

The launcher owns process shutdown, backup validation, the pre-restore safety
copy, staging, atomic database replacement, post-restore startup verification,
rollback, and incomplete-restore recovery.
```

Support-assisted recovery remains a **fallback** for failures that cannot be
resolved automatically; it is not the primary MVP workflow. The user must never
need Git, Python, Node.js, Docker, SQLite tools, GitHub or a terminal.

## Launcher ownership and the closed-backend boundary

The launcher already owns the lifecycle boundary Restore requires: it resolves
the user data directory, takes the `before_migration` backup, runs migrations
before the API is served, starts the uvicorn child against an explicit
`COSMETIC_WORKSHOP_DB_PATH`, and opens the browser only after startup succeeds.
Restore additionally requires that **no backend is running at all**, which a
backend request cannot arrange for itself.

The launcher therefore must prevent a second instance, stop the current backend
cleanly, confirm the database is out of active application use, perform Restore
outside the ordinary API process, start the backend only at the verification
stage, and open the browser only after complete success.

Architecturally excluded:

- replacing the database from a running FastAPI request;
- frontend coordination as the locking mechanism;
- a hidden terminal command as the user workflow;
- direct database replacement while Uvicorn still has the database open.

## Validation before working-database mutation

```text
The staged candidate must pass the complete Restore validation contract
before any mutation, replacement, deletion or migration of the current
working database.
```

Before candidate validation completes, the launcher may create only the isolated
launcher-owned restore-operation directory, the narrow durable operation record,
launcher-owned staging files inside that directory, and local technical logs that
follow the accepted privacy contract. Those writes are **Restore infrastructure**
and do not mutate the current working database or business data.

The selected backup is validated from a **staged read-only copy**. Validation
covers regular-file resolution,
symlink and path-escape refusal, a read-only SQLite open, non-emptiness,
structural checks, the migration-history table, a known ordered migration-ID
prefix with no unknown, duplicated, reordered or skipped IDs, rejection of a
newer-than-current schema, required tables for the recorded schema level,
recognizable `cosmetic-workshop-os` workspace identity, and independence from any
external `-wal`, `-shm` or rollback-journal file. It mutates no business data and
silently repairs nothing.

`PRAGMA quick_check = ok` alone is **never** sufficient proof — see the `CR-004`
evidence in `docs/backup-and-restore.md`. The selected source file is read-only
input and is never modified, renamed, migrated, deleted or rewritten. Restore is
whole-database only.

## Mandatory pre-restore safety copy

Before replacement, the launcher creates and **verifies** a transactionally
consistent copy of the current database through the accepted SQLite Online Backup
engine (ADR 0015) under the canonical reason `before_restore`. `shutil.copy2` is
not reintroduced for SQLite contents. If the current database exists and the
safety copy cannot be created and verified, Restore stops before replacing
anything. The safety copy survives a successful Restore and is never silently
deleted.

## Staging, atomic replacement and the transaction boundary

```text
validate request and source path
→ create an isolated restore-operation directory
→ copy the selected source into a launcher-owned staging file
→ validate the staged candidate
→ create and verify the pre-restore safety copy
→ persist the restore-operation phase
→ atomically replace the working database from a file staged in the same
  filesystem/directory boundary
→ start the application against the exact restored database path
→ run migrations when required
→ verify startup and basic reads
→ mark Restore completed
→ clean only launcher-owned temporary staging files
```

No unrelated foreign file is silently overwritten. The atomic step is the
same-directory filesystem replacement boundary **only**; startup, migration and
verification lie outside it. **Filesystem replacement and SQLite do not form one
database transaction, and no document may claim they do.** That gap is precisely
why durable operation state and rollback are mandatory rather than optional.

## Durable restore-operation state

Exactly one narrow, launcher-owned Restore operation record lives **outside the
working database**, because the working database is what is being replaced. It is
not a workflow engine, job queue, outbox, cloud state store or application-wide
transaction framework.

It holds only an operation ID, safe relative launcher-owned filenames, **the
authoritative `phase`** and timestamps — never database contents, client
information, arbitrary user text, credentials, raw absolute source paths where a
staged relative identity suffices, or SQL errors and stack traces.

**`phase` is the sole authoritative lifecycle field, and it is mutually
exclusive.** Whether replacement occurred and whether rollback completed are
**derived from `phase`**, never persisted as independent authoritative fields
that could contradict it. The accepted vocabulary is exactly twelve
lowercase-ASCII values:

```text
prepared
source_staged
candidate_validated
safety_copy_verified
replacement_intent
replacement_committed
verification_in_progress
completed
aborted
rollback_in_progress
rolled_back
recovery_blocked
```

Terminal phases are `completed`, `aborted`, `rolled_back` and
`recovery_blocked`. Complete definitions, the transition graph, the crash-safe
persistence ordering and the startup recovery matrix are in
`docs/decisions/0016-launcher-assisted-restore.md` § 7 and
`docs/backup-and-restore.md` § 7; this section states only the architectural
boundaries.

## The `replacement_intent` crash boundary

Because filesystem replacement and SQLite are not one transaction, the window

```text
persist replacement intent
→ atomic replacement
→ persist replacement committed
```

cannot be observed from the outside after a crash. The launcher therefore
durably records `replacement_intent` **immediately before** entering the atomic
replacement boundary, and:

```text
A persisted replacement_intent is treated as though replacement may have
occurred, even when the current working file appears unchanged.
```

The launcher must **never** resolve that ambiguity from modification timestamps,
file size alone, filenames, inode identity alone, migration version alone, or the
apparent business contents of the working database. Every such heuristic is
unsound, because the staged candidate is by construction a valid workspace
database. **The conservative outcome is rollback from the verified safety copy.**

The same conservative rule governs `replacement_committed` and
`verification_in_progress`: both leave the restored database **provisional**,
both block ordinary startup, and both recover through rollback. Only a durably
recorded `completed` makes the restored database authoritative, and only then may
the ordinary browser open.

An incomplete operation is detected and resolved **before the ordinary backend
starts**. Every persisted phase has exactly one required startup behaviour, fixed
by the recovery matrix; an interrupted Restore is never ignored, and no
implementation may substitute an alternative state machine.

## Rollback and post-restore verification

Any failure after replacement and before successful completion stops the
partially started backend, preserves diagnostic evidence without exposing it,
durably records `rollback_in_progress` **before** entering the rollback
replacement boundary, restores the safety copy through the same safe replacement
boundary, verifies the rolled-back database starts, durably records `rolled_back`
— or `recovery_blocked` when the result cannot be proved safe — and reports that
Restore did **not** complete.

`rolled_back` is a **failed Restore**: a successful rollback is never reported as
a successful Restore. A failed rollback never continues with an uncertain
database — `recovery_blocked` means the ordinary application does not start,
evidence is preserved, and the user is directed to support-assisted recovery
through a fixed non-technical message. `recovery_blocked` never permits ordinary
startup, and only a separately defined support procedure may leave it.

Restore succeeds only after the backend starts, backend and launcher use the
exact same restored database path, required migrations complete, the database
opens normally, health succeeds, a bounded set of representative read-only
endpoints succeeds, no unexpected fallback database exists, the application can
be restarted against the restored data, the selected source is byte-identical and
the safety backup is available. Those checks run under
`verification_in_progress` and may use the existing backend health and read-only
endpoints; passing them all is what authorizes the durable transition to
`completed`. **The browser UI is not opened into the normal workspace until
`completed` has been durably recorded.**

## Boundaries

Schema: Restore and migration stay distinct. The launcher restores a validated
working copy; the normal startup migration system may then migrate an older
supported schema **on the restored working copy only**. No second migration
framework, and the selected source backup is never migrated.

AuditLog: **no Restore event is authorized**, and `restore.completed` is not
implicitly authorized. Filesystem operation-state evidence is not AuditLog.

Privacy: nothing is uploaded, no network connection is required, user-visible
errors are fixed and non-technical, and technical detail stays in local logs.

Documentation obligation while Restore is unimplemented: the docs must still
honestly explain where backups live, how to recover with support assistance, and
when to contact the developer.

---

## 13. Import/OCR architecture

---

# 13.1. MVP import

MVP:

- CSV;
- XLSX;
- manual column mapping;
- validation;
- preview;
- confirmation.

---

# 13.2. Future OCR

PDF/images:

```text
File upload
→ OCR extraction
→ ImportDraft
→ manual review
→ confirmation
→ apply
```

Hard rule:

```text
OCR output is never trusted automatically.
```

---

## 14. Alert and notification architecture

---

# 14.1. MVP

MVP notifications are in-app only.

```text
AlertGenerationService
→ Alert table
→ Dashboard / Alerts UI
```

---

# 14.2. Future

Future channels:

- email;
- Telegram;
- push;
- cloud notifications.

Поэтому AlertGenerationService не должен зависеть напрямую от Dashboard.

---

## 15. Security and privacy

---

# 15.1. Sensitive client data

Клиентские заметки могут содержать:

- аллергии;
- особенности кожи;
- предпочтения;
- адреса;
- телефоны;
- историю заказов.

Правила:

- не писать чувствительные данные в debug logs;
- не показывать technical traces;
- не экспортировать чувствительные поля без явного выбора;
- backup содержит чувствительные данные, это надо объяснить пользователю.

---

# 15.2. Password

Пароль на вход не обязателен для MVP, но архитектура не должна мешать его добавить.

Future:

```text
Local password
Session token
Encrypted backup
```

---

# 15.3. Localhost access

Backend должен слушать только localhost:

```text
127.0.0.1
```

Не открывать API в локальную сеть без отдельного решения.

---

## 16. Testing architecture

---

# 16.1. Backend tests

Обязательные тесты:

- recipe percent to grams;
- recipe total validation;
- ml to grams with density;
- missing density warning;
- cost calculation;
- tax/margin;
- FEFO selection;
- insufficient stock;
- stock movement;
- production readiness;
- production confirmation transaction;
- cannot produce twice;
- alert generation;
- purchase suggestion;
- import validation;
- audit logging;
- migration from empty DB;
- backup creation.

---

# 16.2. Frontend tests / checks

Минимально:

- build;
- route smoke;
- forms smoke;
- critical manual flows.

Критичные сценарии manual smoke:

```text
Create ingredient
Create lot
Create packaging
Create recipe
Calculate recipe
Create client
Create client recipe
Create order
Check production
Produce order
See stock update
Create backup
```

---

# 16.3. Packaging tests

Для local deployment:

- app starts from package;
- data directory created;
- db created;
- migrations applied;
- browser opens;
- data persists after restart;
- backup works;
- update migration creates backup.

---

## 17. Repository structure

Рекомендуемая структура:

```text
cosmetic-workshop-os/
  AGENTS.md
  README.md
  Makefile

  backend/
    app/
      api/
      domain/
      services/
      repositories/
      models/
      schemas/
      migrations/
      tests/
    pyproject.toml
    alembic.ini

  frontend/
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
    package.json
    vite.config.ts

  launcher/
    macos/
    scripts/

  scripts/
    dev_setup.sh
    dev_start.sh
    build_frontend.sh
    build_backend.sh
    package_macos.sh
    start_local.sh
    create_backup.sh
    restore_backup.sh

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

  help/
    how-to-create-recipe.md
    how-to-add-ingredient.md
    how-to-create-order.md
    how-to-produce-order.md
    how-to-create-backup.md
    what-is-density.md
    what-is-lot.md
    what-is-client-recipe.md
```

---

## 18. MVP acceptance architecture checklist

MVP архитектурно готов, если:

```text
[ ] Приложение запускается локально
[ ] Данные хранятся отдельно от кода
[ ] Есть миграции
[ ] Есть backup
[ ] Перед миграцией создается auto-backup
[ ] Есть first-run wizard
[ ] Есть onboarding checklist
[ ] Есть понятные empty states
[ ] Есть help center
[ ] Есть ClientWish/ClientFeedback
[ ] Есть RecipeTemplate/RecipeVersion/ClientRecipe
[ ] Есть Ingredient/IngredientLot/StockMovement
[ ] Есть Order/ProductionBatch
[ ] Производство transactional
[ ] Расчеты через Decimal
[ ] ml→g через density
[ ] Missing density дает warning
[ ] Алерты отделены от UI
[ ] Импорт через ImportDraft
[ ] AuditLog пишет важные действия
[ ] Пользователь может экспортировать данные
[ ] Пакет можно установить удаленно
[ ] Пользователь не обязан пользоваться GitHub/terminal/Docker
```

---

## 19. Что нельзя делать

Нельзя:

- делать frontend-only бизнес-логику расчетов;
- хранить базу внутри репозитория;
- заставлять пользователя запускать проект из GitHub;
- использовать Docker как обязательный пользовательский способ;
- менять исторические версии рецептов без следа;
- списывать остатки без StockMovement;
- производить заказ без confirmation;
- импортировать данные без preview;
- доверять OCR без ручной проверки;
- удалять бизнес-данные без audit;
- скрывать warnings по плотности;
- молча считать 1 мл = 1 г без предупреждения;
- показывать клиентке stack trace;
- делать UI как техническую админку.

---

## 20. Что можно отложить на v2

Можно отложить:

- cloud sync;
- phone read-only;
- OCR PDF/images;
- branded PDF;
- этикетки;
- attachments UI;
- certification documents;
- roles and users;
- password;
- encrypted backup;
- advanced analytics;
- auto-update;
- signed .dmg;
- external notifications.

Но архитектура MVP не должна блокировать эти направления.

---

## 21. Итоговая архитектурная формула

```text
cosmetic-workshop-os =
  packaged local app
  + local launcher
  + separated user data directory
  + browser UI
  + backend API
  + domain services
  + SQLite with migrations
  + recipe/client/inventory/order/production core
  + alerts/purchases/import/export
  + onboarding/help layer
  + backup/update safety
  + future cloud/mobile/OCR path
```

Главный критерий архитектуры:

```text
Пользователь должен получить не репозиторий и не техническую админку,
а локальную рабочую систему, которую можно открыть, понять, использовать,
обновить и не потерять свои рецепты, клиентов и историю производства.
```
