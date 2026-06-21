# cosmetic-workshop-os - Frontend concept

Проект: **cosmetic-workshop-os**  
Клиентское название: **Мастерская косметолога**  
Документ: **docs/frontend-concept.md**  
Версия: **0.1 draft**  
Статус: **frontend contract для реализации через Codex**

---

## 1. Назначение документа

Этот документ фиксирует фронтовую концепцию проекта `cosmetic-workshop-os`.

Документ нужен, чтобы:

- Codex не строил техническую админку вместо понятного рабочего продукта;
- frontend развивался по roadmap, без преждевременного ERP-раздувания;
- интерфейс оставался local-first, desktop-first и понятным для нетехнического пользователя;
- бизнес-логика не переносилась во frontend;
- routes, layout, компоненты, состояния, DTO и UX-правила были согласованы до реализации;
- MVP можно было собирать маленькими проверяемыми PR.

Документ должен использоваться вместе с:

```text
AGENTS.md
README.md
docs/product-spec.md
docs/architecture.md
docs/roadmap.md
docs/domain-model.md
docs/ui-ux-guidelines.md
docs/ui-ux-contract.md
docs/import-format.md
docs/backup-and-restore.md
docs/local-install.md
docs/user-guide.md
docs/mvp-smoke-checklist.md
```

---

## 2. Главная фронтовая идея

Frontend должен ощущаться не как складская админка, не как CRM и не как бухгалтерская система.

Frontend должен ощущаться как **рабочий стол косметической мастерской**:

```text
открыла приложение
→ поняла, что сделать сегодня
→ увидела заказы и алерты
→ создала или открыла рецепт
→ проверила компоненты и тару
→ сделала заказ
→ проверила возможность изготовления
→ подтвердила производство
→ увидела списание, маржу и следующие действия
```

Главный центр продукта:

```text
Рецепт
→ версия рецепта
→ индивидуальный рецепт клиента
→ заказ
→ проверка производства
→ производственная партия
→ списание склада
→ алерты и закупки
```

Интерфейс должен постоянно помогать пользователю отвечать на вопросы:

```text
Что сделать сегодня?
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
```

---

## 3. Product UX principles

### 3.1. Не техническая админка

Пользователь не обязан понимать технические сущности, ID, database errors, stack traces, DTO, migration или backend.

Плохо:

```text
ValidationError: decimal parsing failed
```

Хорошо:

```text
В поле “Остаток” нужно указать число. Например: 30 или 30,5.
```

### 3.2. Каждый экран подсказывает следующий шаг

У каждого ключевого экрана должен быть понятный next action:

- создать первый рецепт;
- добавить партию компонента;
- создать клиента;
- создать индивидуальный рецепт;
- проверить заказ;
- изготовить заказ;
- создать backup;
- открыть справку.

### 3.3. Empty states обязательны

Нельзя показывать пустую таблицу без объяснения.

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

### 3.4. Сложные поля объясняются рядом

Подсказки нужны для:

- плотности;
- минимального остатка;
- партии компонента;
- версии рецепта;
- индивидуального рецепта;
- срока годности;
- себестоимости;
- налога;
- маржи;
- производственной партии;
- FEFO-списания;
- backup.

### 3.5. Опасные действия подтверждаются

Confirmation dialog обязателен для:

- подтверждения производства;
- списания остатков;
- ручной корректировки склада;
- архивирования сущности;
- применения импорта;
- восстановления backup;
- миграции или обновления;
- удаления demo data.

### 3.6. Frontend не владеет бизнес-логикой

Frontend может:

- отображать данные;
- валидировать форму до отправки;
- показывать предупреждения;
- помогать заполнить данные;
- вызывать backend API;
- показывать structured result от backend.

Frontend не должен:

- рассчитывать финальную себестоимость как источник истины;
- делать FEFO selection как источник истины;
- списывать склад локально;
- менять исторические версии рецептов;
- подтверждать производство без backend transaction;
- нормализовать проценты рецепта без явного действия пользователя;
- скрывать warnings от backend.

Источник истины для расчетов и производственных действий:

```text
Backend API
→ Domain services
→ Repositories
→ Database
```

---

## 4. Frontend scope by MVP

### 4.1. MVP frontend включает

```text
Dashboard
Recipes
Recipe versions
Recipe calculation UI
Clients
Client recipes
Client wishes
Client feedback
Orders
Stock ingredients
Ingredient lots
Packaging
Stock movements
Production readiness
Production confirmation
Alerts
Purchase suggestions
Import wizard
Reports basic
Settings
Backups UI
Audit log viewer
Onboarding
Guided checklist
Demo data mode
Help center
```

### 4.2. MVP frontend не включает

```text
Полноценную бухгалтерию
Полноценную CRM с лидами и сделками
Роли и пользователей
Cloud sync UI
Mobile app
OCR UI для PDF/images
Сертификаты и сложный документ-центр
Branded PDF designer
Advanced BI
LTV dashboard
Auto-update UI с загрузкой обновлений
```

### 4.3. V2+ направления

В будущем можно добавить:

```text
Attachments UI
OCR import drafts
Phone read-only view
Cloud backup
Cloud sync
Certification documents
Advanced analytics
Signed installer and auto-update
Roles and local password
```

Но MVP routes и компоненты не должны заранее строить весь V2-интерфейс.

---

## 5. MVP route map

MVP route map должен быть компактным и соответствовать roadmap.

```text
/
├─ /onboarding
├─ /app
│  ├─ /dashboard
│  ├─ /recipes
│  ├─ /recipes/new
│  ├─ /recipes/:recipeId
│  ├─ /recipe-versions/:versionId
│  ├─ /clients
│  ├─ /clients/new
│  ├─ /clients/:clientId
│  ├─ /client-recipes/:clientRecipeId
│  ├─ /orders
│  ├─ /orders/new
│  ├─ /orders/:orderId
│  ├─ /stock
│  ├─ /stock/ingredients
│  ├─ /stock/ingredients/:ingredientId
│  ├─ /stock/lots
│  ├─ /stock/movements
│  ├─ /packaging
│  ├─ /purchases
│  ├─ /production
│  ├─ /production/batches
│  ├─ /production/batches/:batchId
│  ├─ /alerts
│  ├─ /import
│  ├─ /reports
│  ├─ /settings
│  ├─ /settings/backups
│  ├─ /settings/audit-log
│  └─ /help
└─ /not-found
```

### 5.1. Routes to defer

Эти routes не входят в MVP:

```text
/auth
/app/crm/leads
/app/crm/deals
/app/crm/communications
/app/finance/accounts
/app/finance/payables
/app/finance/receivables
/app/finance/cashflow
/app/finance/tax
/app/documents/certificates
/app/documents/labels
/app/reports/client-ltv
/app/reports/advanced-bi
/app/formulas/ph-check
/app/formulas/yield-estimator
/app/settings/users
/app/settings/roles
```

Если Codex добавляет такие routes без отдельного scope, это считается scope creep.

---

## 6. Navigation model

Основная навигация в MVP:

```text
Главная
Рецепты
Клиенты
Заказы
Запасы
Тара
Закупки
Производство
Алерты
Импорт
Отчеты
Настройки
Помощь
```

### 6.1. Sidebar

Sidebar отвечает за стабильную навигацию.

В sidebar должны быть:

- основное меню;
- быстрые действия;
- индикаторы критичных алертов;
- ссылка на help center;
- ссылка на настройки;
- статус backup, если есть критичное напоминание.

### 6.2. Topbar

Topbar отвечает за контекст текущего экрана.

В topbar должны быть:

- breadcrumbs;
- глобальный поиск, если реализован;
- основные действия текущей страницы;
- уведомления;
- состояние backend, если есть проблема.

### 6.3. Right context panel

Right context panel можно использовать на detail pages.

Содержимое:

- быстрые действия;
- связанные сущности;
- последние события;
- предупреждения;
- краткая себестоимость;
- готовность производства;
- подсказки по следующему шагу.

---

## 7. Layout architecture

### 7.1. App shell

```text
<AppRoot>
  <Providers>
    <Router />
    <AppShell>
      <Sidebar />
      <MainColumn>
        <Topbar />
        <PageViewport />
      </MainColumn>
    </AppShell>
  </Providers>
</AppRoot>
```

### 7.2. Providers

```text
<ThemeProvider />
<QueryProvider />
<RouterProvider />
<ErrorBoundary />
<ToastProvider />
```

AuthProvider не является обязательным для MVP, если авторизация отложена. Нельзя строить полноценный roles/users слой без отдельного roadmap scope.

### 7.3. Page layouts

#### List page

```text
<ListPageLayout>
  <PageHeader />
  <FilterBar />
  <SavedViewsBar optional />
  <BulkActionsBar optional />
  <DataTable />
  <Pagination />
</ListPageLayout>
```

#### Entity page

```text
<EntityPageLayout>
  <EntityHeader />
  <StatusStrip />
  <EntityTabs />
  <EntityMainPanel />
  <EntitySidePanel optional />
  <ActivityTimeline optional />
</EntityPageLayout>
```

#### Wizard page

```text
<WizardLayout>
  <StepSidebar />
  <StepContent />
  <ValidationPanel />
  <StickyFooterActions />
</WizardLayout>
```

Wizard используется для:

- first-run onboarding;
- создания производственной партии, если нужен пошаговый режим;
- импорта CSV/XLSX;
- восстановления backup, если restore реализован.

---

## 8. Key screens

## 8.1. Dashboard

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

Блоки MVP:

```text
OnboardingChecklist
ActiveOrders
OrdersWaitingForMaterials
AlertsPanel
PurchaseSuggestionsPanel
QuickActions
BackupReminder
```

Dashboard не должен быть BI-экраном в MVP. Его задача - ежедневная работа, а не аналитика ради аналитики.

---

## 8.2. Recipes list

Назначение:

```text
Найти рецепт, создать рецепт, увидеть статус и проблемы.
```

Компоненты:

```text
RecipeTable
RecipeFilters
RecipeStatusBadge
RecipeWarningBadge
CreateRecipeButton
EmptyRecipesState
```

Показывать:

- название;
- категорию;
- статус;
- последнюю версию;
- сумму процентов;
- предупреждения;
- дату обновления;
- быстрые действия.

---

## 8.3. Recipe detail

Карточка рецепта - один из главных рабочих экранов.

Вкладки:

```text
Обзор
Формула
Версии
Расчет
Партии
История
```

MVP может объединять часть вкладок, но пользователь должен видеть:

- название рецепта;
- статус;
- текущую версию;
- список ингредиентов;
- фазы;
- проценты;
- сумму рецепта;
- расчет граммов на выбранный объем;
- предупреждения по плотности и валидности;
- оценочную себестоимость;
- кнопку создания новой версии;
- связанные заказы или партии, если уже есть.

Пример структуры:

```text
<RecipePage>
  <RecipeHeader />
  <RecipeStatusStrip />
  <RecipeTabs />
  <FormulaWorkspace />
  <RecipeCalculationPanel />
  <RecipeWarningsPanel />
  <RecipeActivityPanel />
</RecipePage>
```

Важное правило:

```text
Frontend не пересчитывает рецепт как источник истины.
Frontend отправляет параметры в backend calculation endpoint и показывает результат.
```

---

## 8.4. Client detail

Карточка клиента - рабочий центр клиента.

Вкладки:

```text
Профиль
Заказы
Индивидуальные рецепты
Пожелания
Обратная связь
История
Файлы
```

MVP может отложить полноценный UI файлов, но вкладка или future placeholder допустимы, если не раздувает scope.

Ключевые действия:

- создать заказ;
- создать индивидуальный рецепт;
- добавить пожелание;
- добавить обратную связь;
- открыть историю заказов;
- перейти к связанному рецепту.

Нельзя показывать чувствительные заметки в технических логах или error traces.

---

## 8.5. Client recipe detail

Индивидуальный рецепт клиента - first-class сущность.

Экран должен показывать:

- клиента;
- исходный базовый рецепт и версию;
- причину индивидуализации;
- формулу;
- расчет;
- связанные пожелания;
- обратную связь;
- связанные заказы.

Правило:

```text
Изменение индивидуального рецепта не меняет базовый рецепт.
```

---

## 8.6. Orders list and order detail

Заказ - центральный операционный объект.

Order detail должен показывать:

- клиента;
- рецепт или индивидуальный рецепт;
- целевой объем;
- тару;
- цену продажи;
- оценочную себестоимость;
- налог;
- маржу;
- статус;
- следующий шаг.

Ключевые действия:

```text
Проверить изготовление
Изготовить
Отменить
Отметить доставленным
Добавить обратную связь
```

Кнопка “Изготовить” доступна только после readiness check и confirmation dialog.

---

## 8.7. Stock and packaging

Склад должен быть понятен без бухгалтерских терминов.

MVP разделяется на:

```text
Компоненты
Партии компонентов
Движения склада
Тара
```

Компонент должен показывать:

- название;
- INCI, если есть;
- категорию;
- единицу;
- плотность;
- минимальный остаток;
- текущий остаток;
- партии;
- сроки годности;
- движения.

Партия компонента должна показывать:

- дату покупки;
- начальное количество;
- остаток;
- цену;
- срок годности;
- поставщика;
- статус.

Все изменения склада идут через StockMovement.

---

## 8.8. Production UI

Production UI в MVP живет в основном внутри Order detail и ProductionBatch detail.

Readiness result должен показывать:

```text
Можно изготовить или нельзя
Что блокирует производство
Какие есть предупреждения
Какие компоненты нужны
Какие партии будут использованы
Сколько тары нужно
Какая себестоимость
Какая маржа
```

Before confirmation показывать:

```text
Что будет списано
Какие партии будут использованы
Как изменится статус заказа
Какая производственная партия будет создана
```

Если backend возвращает ошибку, frontend показывает human-readable error, без stack trace.

---

## 8.9. Alerts and purchases

Alerts должны быть понятными и actionable.

Alert card показывает:

- тип;
- severity;
- сообщение;
- связанную сущность;
- причину;
- рекомендуемое действие;
- кнопки “решено”, “скрыть”, “открыть”.

PurchaseSuggestion показывает:

- что купить;
- сколько купить;
- почему купить;
- связано ли с заказом;
- можно ли отметить как купленное.

---

## 8.10. Import wizard

Импорт всегда пошаговый.

```text
1. Загрузить файл
2. Выбрать тип данных
3. Сопоставить колонки
4. Проверить preview
5. Исправить ошибки
6. Подтвердить применение
7. Увидеть итог
```

Правило:

```text
Frontend не применяет импорт напрямую.
Frontend работает с ImportSource и ImportDraft через backend API.
```

---

## 8.11. Reports

Reports в MVP простые.

MVP reports:

```text
Текущие остатки
Мало остатков
Скоро истекает срок
Истек срок
Заказы за период
Производство за период
Себестоимость и маржа по заказам
Расход компонентов за период
История клиента
```

Не делать в MVP:

```text
Advanced BI
LTV
Cohort retention
Полноценный cashflow
Полноценный P&L
```

---

## 8.12. Settings

Settings должны быть понятны пользователю.

MVP settings:

```text
Налоговая ставка
Срок предупреждения о годности
Минимальные остатки
Категории рецептов
Категории компонентов
Роли компонентов
Фазы рецептов
Категории тары
Напоминание о backup
Путь к папке данных
Backup
Audit log
```

Путь к данным показывается явно, потому что приложение local-first.

---

## 8.13. Help center

Help center работает офлайн.

MVP articles:

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
Что такое партия компонента
Что такое индивидуальный рецепт
```

Ссылки на help должны быть контекстными:

- рядом со сложными полями;
- в empty states;
- в onboarding;
- в error messages, если ошибка требует объяснения.

---

## 9. Frontend architecture

## 9.1. Recommended stack

MVP frontend stack:

```text
React
TypeScript
Vite
React Router
TanStack Query
Zustand
React Hook Form
Zod
```

Optional:

```text
Redux Toolkit only if explicit event replay/debug need appears later
```

Не использовать Redux Toolkit для всего приложения по умолчанию.

---

## 9.2. Folder structure

Использовать feature-sliced подход, согласованный с архитектурой проекта.

```text
frontend/
  src/
    app/
      routes/
      providers/
      layout/
      error-boundaries/
    pages/
      dashboard/
      recipes/
      clients/
      orders/
      stock/
      packaging/
      purchases/
      production/
      alerts/
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
      purchase-suggestions/
      backup-reminder/
    features/
      create-recipe/
      calculate-recipe/
      create-client/
      create-client-recipe/
      manage-client-wish/
      manage-client-feedback/
      create-order/
      check-production-readiness/
      confirm-production/
      import-wizard/
      create-backup/
      resolve-alert/
    entities/
      recipe/
      recipe-version/
      client/
      client-recipe/
      client-wish/
      client-feedback/
      order/
      ingredient/
      ingredient-lot/
      packaging/
      stock-movement/
      production-batch/
      alert/
      purchase-suggestion/
      backup/
      audit-log/
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
      types/
```

### 9.3. Layer rules

```text
app      - providers, routing, app shell
pages    - route-level composition
widgets  - reusable domain blocks
features - user actions and flows
entities - domain DTOs, UI fragments, labels
shared   - generic UI, api client, utils
```

Rules:

- `shared` не знает о домене;
- `entities` не вызывает сложные flows;
- `features` может вызывать API mutation;
- `pages` собирает экран из widgets/features/entities;
- backend business rules не дублируются во frontend как источник истины.

---

## 10. State management

## 10.1. Split

```text
Server state: TanStack Query
UI state: Zustand
Form state: React Hook Form + Zod
URL state: search params for filters where useful
```

## 10.2. Zustand stores

```ts
type UiStore = {
  sidebarCollapsed: boolean
  rightPanelOpen: boolean
  commandPaletteOpen: boolean
  currentModal: string | null
}

type NavigationStore = {
  breadcrumbs: Breadcrumb[]
  recentEntities: RecentEntity[]
  pinnedViews: SavedViewRef[]
}

type RecipeDraftStore = {
  currentRecipeId: string | null
  dirty: boolean
  validationState: RecipeValidationState | null
}

type FiltersStore = {
  recipeFilters: RecipeFilters
  clientFilters: ClientFilters
  orderFilters: OrderFilters
  stockFilters: StockFilters
}

type NotificationsStore = {
  unreadCount: number
  localNotifications: AppNotification[]
}
```

Не хранить в Zustand полные server entities, если их уже ведет TanStack Query.

---

## 11. API and DTO strategy

## 11.1. DTO-first frontend

Frontend должен работать через typed DTO contracts.

Не использовать Prisma schema как frontend contract.

Правильная схема:

```text
Backend SQLAlchemy models
→ Backend Pydantic schemas
→ OpenAPI or documented DTO
→ Frontend TypeScript types
→ UI rendering
```

## 11.2. API client modules

```text
frontend/src/shared/api/
  http-client.ts
  errors.ts
  health.api.ts
  settings.api.ts
  onboarding.api.ts
  recipes.api.ts
  client-recipes.api.ts
  clients.api.ts
  client-wishes.api.ts
  client-feedback.api.ts
  ingredients.api.ts
  ingredient-lots.api.ts
  packaging.api.ts
  stock-movements.api.ts
  orders.api.ts
  production.api.ts
  alerts.api.ts
  purchases.api.ts
  imports.api.ts
  exports.api.ts
  backups.api.ts
  reports.api.ts
  audit-logs.api.ts
  help.api.ts
```

## 11.3. Example DTOs

```ts
type RecipeSummaryDto = {
  id: string
  name: string
  category: string | null
  status: RecipeStatus
  currentVersionId: string | null
  totalPercentStatus: 'valid_100' | 'below_100' | 'above_100' | 'unknown'
  warningCount: number
  updatedAt: string
}

type RecipeCalculationResultDto = {
  recipeVersionId: string
  finalBatchGrams: string
  totalPercent: string
  totalPercentStatus: 'valid_100' | 'below_100' | 'above_100'
  rows: RecipeCalculationRowDto[]
  estimatedComponentCost: string
  warnings: DomainWarningDto[]
}

type ProductionReadinessDto = {
  orderId: string
  canProduce: boolean
  blockingIssues: DomainIssueDto[]
  warnings: DomainWarningDto[]
  selectedIngredientLots: SelectedLotDto[]
  requiredPackaging: RequiredPackagingDto[]
  estimatedCost: string
  estimatedTax: string
  estimatedMargin: string
  estimatedMarginPercent: string
}
```

## 11.4. Error contract

Frontend expects structured errors:

```ts
type ApiErrorDto = {
  code: string
  message: string
  humanMessage: string
  details?: Record<string, unknown>
  fieldErrors?: FieldErrorDto[]
}
```

Frontend показывает `humanMessage`, а не raw technical message.

---

## 12. Query keys

Query keys должны быть стабильными.

```ts
['health']
['settings']
['onboarding-state']
['dashboard']
['recipes', filters]
['recipe', recipeId]
['recipe-version', versionId]
['recipe-calculation', versionId, finalBatchGrams]
['clients', filters]
['client', clientId]
['client-recipes', clientId]
['client-recipe', clientRecipeId]
['client-wishes', clientId]
['client-feedback', clientId]
['orders', filters]
['order', orderId]
['production-readiness', orderId]
['ingredients', filters]
['ingredient', ingredientId]
['ingredient-lots', filters]
['packaging', filters]
['stock-movements', filters]
['alerts', filters]
['purchase-suggestions', filters]
['imports', filters]
['reports', reportType, filters]
['backups']
['audit-logs', filters]
['help-articles']
['help-article', slug]
```

Mutation success должен invalidаte только связанные query keys, а не весь cache без причины.

---

## 13. Component system

## 13.1. Shared UI primitives

```text
Button
IconButton
Input
Textarea
Select
Combobox
Checkbox
RadioGroup
DatePicker
MoneyInput
DecimalInput
PercentInput
UnitInput
Tabs
Dialog
Drawer
Popover
Tooltip
Badge
StatusBadge
SeverityBadge
Skeleton
EmptyState
HumanErrorMessage
ConfirmationDialog
```

## 13.2. Data display

```text
DataTable
SimpleTable
StatCard
WarningList
IssueList
AuditTimeline
ActivityFeed
DocumentPreview
CostBreakdown
```

## 13.3. Domain widgets

```text
RecipeVersionSwitcher
RecipeIngredientTable
FormulaPhaseEditor
RecipeCalculationPanel
DensityWarningPanel
ClientSummaryCard
ClientWishList
ClientFeedbackList
ClientRecipeList
OrderStatusStrip
OrderReadinessPanel
StockAvailabilityPanel
IngredientLotPicker
ProductionConfirmationPanel
AlertCard
PurchaseSuggestionCard
BackupReminderCard
OnboardingChecklist
```

## 13.4. Page composites

```text
DashboardPage
RecipeListPage
RecipeDetailPage
ClientDetailPage
OrderDetailPage
StockPage
ProductionBatchPage
ImportWizardPage
SettingsPage
HelpArticlePage
```

---

## 14. Status and labels

Все статусы в UI показываются на русском языке.

Examples:

```text
new -> Новый
waiting_for_materials -> Ждет компоненты
ready_to_produce -> Можно изготовить
in_progress -> В работе
produced -> Изготовлен
delivered -> Передан клиенту
cancelled -> Отменен
archived -> В архиве
```

Severity labels:

```text
info -> Информация
warning -> Внимание
critical -> Критично
resolved -> Решено
```

Технические enum values не показываются пользователю.

---

## 15. Human-readable validation

Frontend field validation нужна для быстрого feedback, но backend остается источником истины.

Examples:

```text
Введите количество. Например: 30 или 30,5.
Срок годности не может быть раньше даты покупки.
Остаток партии не может быть больше начального количества.
Цена продажи нужна, чтобы посчитать маржу.
Плотность нужна для перевода мл в граммы.
```

Ошибки backend должны маппиться в понятный текст.

---

## 16. Onboarding and learning UX

## 16.1. First-run wizard

Route:

```text
/onboarding
```

Steps:

```text
1. Добро пожаловать
2. Где хранить данные
3. Налоговая ставка
4. Напоминание о backup
5. Создать демо-данные
6. Начать работу
```

## 16.2. Guided checklist

Dashboard checklist:

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

Checklist должен:

- отмечаться автоматически;
- скрываться пользователем;
- восстанавливаться из настроек;
- не мешать после завершения.

## 16.3. Demo mode

Demo data должны быть явно помечены.

Правила:

- demo data можно удалить;
- удаление demo data не затрагивает реальные данные;
- demo production не должна смешиваться с реальной историей без явной маркировки.

---

## 17. Accessibility and usability

Минимальные правила:

- keyboard navigation для основных форм;
- видимый focus state;
- labels у полей;
- aria-label для icon buttons;
- ошибки рядом с полем;
- понятные заголовки страниц;
- responsive behavior для узкого экрана, но desktop-first;
- таблицы не должны ломаться на маленьком экране, допустим horizontal scroll.

---

## 18. Implementation sequence alignment

Frontend должен следовать roadmap.

```text
PR1  App shell and base navigation
O1   First-run wizard
O2   Empty states and contextual help
UX1  Human-friendly UI system contract
PR7  Inventory UI
PR10 Recipe UI
PR11 Clients UI
PR12 Client recipes UI
PR12b Wishes and feedback UI
PR14 Orders UI
PR17 Production UI
PR20 Dashboard
O3   Guided setup checklist
O4   Demo data mode
O5   Help center
PR22 Import UI
PR24 Reports UI
PR26 Settings UI
PR27 Audit viewer
```

Нельзя реализовывать frontend-экраны, для которых нет backend/API contract, кроме placeholder в рамках отдельного PR scope.

---

## 19. Frontend acceptance checklist

Frontend MVP считается готовым, если пользователь может:

```text
[ ] открыть приложение локально
[ ] пройти first-run wizard
[ ] увидеть dashboard с понятными следующими шагами
[ ] создать backup
[ ] создать компонент
[ ] создать партию компонента
[ ] создать тару
[ ] создать базовый рецепт
[ ] создать версию рецепта
[ ] рассчитать граммы по процентам
[ ] увидеть warning по плотности, если density отсутствует
[ ] создать клиента
[ ] создать индивидуальный рецепт клиента
[ ] добавить пожелание клиента
[ ] добавить обратную связь клиента
[ ] создать заказ
[ ] проверить готовность производства
[ ] увидеть, чего не хватает
[ ] подтвердить производство через confirmation dialog
[ ] увидеть списание склада
[ ] увидеть производственную партию
[ ] увидеть алерты
[ ] увидеть закупочные рекомендации
[ ] импортировать CSV/XLSX через preview
[ ] выгрузить данные
[ ] открыть audit log
[ ] открыть help article
[ ] перезапустить приложение без потери данных
```

---

## 20. Anti-patterns

Нельзя:

- строить UI как техническую админку;
- показывать пользователю raw IDs как основной текст;
- показывать stack traces;
- делать frontend-only расчеты как источник истины;
- делать frontend-only списание склада;
- делать production confirmation без backend transaction;
- добавлять Prisma как frontend data contract;
- строить полноценную CRM в MVP;
- строить полноценную бухгалтерию в MVP;
- добавлять roles/users без отдельного scope;
- делать documents center раньше PDF PR;
- добавлять cloud/mobile/OCR routes раньше V2 scope;
- применять импорт без preview и confirmation;
- скрывать warnings по плотности;
- молча считать 1 мл = 1 г;
- удалять бизнес-данные без confirmation и audit;
- перегружать dashboard advanced charts.

---

## 21. Final frontend formula

```text
frontend concept =
  human-friendly local app shell
  + recipe/client/order centered navigation
  + typed API DTO contracts
  + TanStack Query for server state
  + Zustand for UI state
  + backend-owned business logic
  + empty states and contextual help
  + onboarding and guided checklist
  + production-safe confirmation flows
  + simple daily dashboard
  + strict MVP routes
  + V2 deferred expansion
```

Главный критерий:

```text
Пользователь должен открыть приложение и понять, что делать дальше,
не чувствуя, что перед ним техническая база данных, ERP или бухгалтерская система.
```

## PR8 first-run onboarding skeleton

The first-run surface is intentionally small and non-technical. The Dashboard may show a welcome card, a local-data explanation, and a placeholder checklist for the first workspace steps: welcome, data location, first ingredient, first recipe, first client, first order, and first backup. These checklist steps do not create business records yet; they only help the user understand the recommended order of work while later roadmap PRs add the real flows.

If the backend is unavailable, the shell must still render a warm fallback explanation instead of a technical error. The copy should continue to explain that the product is a local workspace and that data belongs on the user's computer.
