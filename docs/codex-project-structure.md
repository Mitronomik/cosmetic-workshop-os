# cosmetic-workshop-os — структура проектной памяти для Codex

Документ: `docs/codex-project-structure.md`  
Проект: `cosmetic-workshop-os`  
Клиентское название: «Мастерская косметолога»  
Назначение: зафиксировать, как правильно упаковать проектную логику, архитектуру, roadmap, прогресс и правила работы в Markdown-файлы для Codex Web / AI-agent workflow.

---

## 1. Главная идея

Проект должен быть организован не только как кодовая база, но и как **проектная память**.

Codex должен каждый раз быстро понимать:

- что это за продукт;
- для кого он делается;
- какие архитектурные решения уже приняты;
- какой текущий этап разработки;
- что уже сделано;
- что делать следующим PR;
- какие ограничения нельзя нарушать;
- где лежит подробная документация;
- как писать код, тесты, миграции и UI.

Главный принцип:

```text
AGENTS.md = короткий обязательный контракт для агента
docs/ = долговременная проектная документация
state/ = текущая память проекта и ход работ
backend/frontend/launcher AGENTS.md = локальные правила для конкретных зон кода
```

Не нужно превращать `AGENTS.md` в огромную энциклопедию.  
Он должен быть маршрутизатором и набором жестких правил.  
Подробности должны лежать в `docs/`.

---

## 2. Рекомендуемая структура репозитория

```text
cosmetic-workshop-os/
├── AGENTS.md
├── README.md
├── Makefile
├── CONTRIBUTING.md
├── code_review.md
│
├── backend/
│   ├── AGENTS.md
│   └── app/
│       ├── api/
│       ├── domain/
│       ├── services/
│       ├── repositories/
│       ├── models/
│       ├── schemas/
│       ├── migrations/
│       └── tests/
│
├── frontend/
│   ├── AGENTS.md
│   └── src/
│       ├── app/
│       ├── pages/
│       ├── widgets/
│       ├── features/
│       ├── entities/
│       └── shared/
│
├── launcher/
│   ├── AGENTS.md
│   └── macos/
│
├── scripts/
│   ├── dev_setup.sh
│   ├── dev_start.sh
│   ├── build_frontend.sh
│   ├── build_backend.sh
│   ├── package_macos.sh
│   ├── start_local.sh
│   ├── create_backup.sh
│   └── restore_backup.sh
│
├── docs/
│   ├── AGENTS.md
│   ├── product-spec.md
│   ├── architecture.md
│   ├── roadmap.md
│   ├── implementation-plan.md
│   ├── domain-model.md
│   ├── domain-glossary.md
│   ├── api.md
│   ├── testing.md
│   ├── ui-ux-contract.md
│   ├── import-format.md
│   ├── deployment.md
│   ├── packaging.md
│   ├── local-install.md
│   ├── user-install.md
│   ├── remote-install-checklist.md
│   ├── update-guide.md
│   ├── backup-and-restore.md
│   ├── user-guide.md
│   ├── mvp-smoke-checklist.md
│   └── decisions/
│       ├── 0001-local-first.md
│       ├── 0002-sqlite-mvp.md
│       ├── 0003-recipe-versioning.md
│       ├── 0004-user-data-directory.md
│       └── 0005-import-drafts.md
│
├── state/
│   ├── progress.md
│   ├── handoff.md
│   ├── current-focus.md
│   └── change-requests.md
│
└── help/
    ├── how-to-create-recipe.md
    ├── how-to-add-ingredient.md
    ├── how-to-create-client.md
    ├── how-to-create-order.md
    ├── how-to-produce-order.md
    ├── how-to-create-backup.md
    ├── what-is-density.md
    ├── what-is-lot.md
    └── what-is-client-recipe.md
```

---

## 3. Роли основных файлов

### `AGENTS.md`

Главный контракт для Codex.

Содержит:

- короткое описание проекта;
- список документов, которые нужно читать;
- hard rules;
- запреты;
- команды;
- PR workflow;
- требование обновлять `state/`.

`AGENTS.md` не должен хранить все ТЗ.  
Он должен направлять агента к нужным документам.

---

### `README.md`

Файл для людей.

Содержит:

- что это за проект;
- кому он нужен;
- как запустить dev-режим;
- где документация;
- текущий статус.

---

### `docs/architecture.md`

Главный архитектурный контракт.

Содержит:

- local-first;
- local launcher;
- user data directory;
- backend/frontend/domain/database;
- onboarding;
- help layer;
- ClientWish/Feedback;
- update safety;
- future cloud/mobile/OCR path.

---

### `docs/roadmap.md`

Итоговый roadmap реализации через Codex.

Содержит:

- последовательность PR;
- scope;
- non-goals;
- backend/frontend requirements;
- tests;
- acceptance criteria.

---

### `docs/implementation-plan.md`

Короткий план ближайших 3-5 PR.

Нужен, чтобы Codex не уходил дальше текущего окна.

Пример:

```markdown
# Implementation Plan

## Current window

- PR0 — Docs contract
- PR1 — App shell
- PR2 — DB + settings + audit
- D1 — User data directory
- D2 — Local launcher

## Do now

PR1 — App shell

## Do not start yet

- Inventory
- Recipes
- Orders
- Production
- Cloud
- OCR
```

---

### `docs/domain-model.md`

Подробное описание сущностей.

Содержит:

- Client;
- ClientWish;
- ClientFeedback;
- RecipeTemplate;
- RecipeVersion;
- ClientRecipe;
- Ingredient;
- IngredientLot;
- PackagingItem;
- StockMovement;
- Order;
- ProductionBatch;
- Alert;
- PurchaseSuggestion;
- ImportSource;
- ImportDraft;
- AuditLog;
- OnboardingState;
- BackupRecord;
- UpdateLog;
- Attachment.

---

### `docs/domain-glossary.md`

Словарь домена.

Нужен, чтобы Codex не путал термины.

Пример:

```text
RecipeTemplate — базовый рецепт
RecipeVersion — конкретная версия базового рецепта
ClientRecipe — индивидуальная формула клиента
IngredientLot — партия компонента
StockMovement — движение склада
ProductionBatch — факт изготовления
FEFO — first expired, first out
Density — плотность для перевода мл в граммы
ImportDraft — черновик импорта
```

---

### `docs/ui-ux-contract.md`

Контракт человекопонятного UI.

Фиксирует:

- не показывать технические ошибки;
- каждый пустой экран объясняет следующий шаг;
- опасные действия через confirmation;
- подсказки к сложным полям;
- карточка клиента как рабочий центр;
- onboarding checklist;
- help center;
- статусы на русском;
- visual severity для алертов.

---

### `docs/api.md`

API-контракты:

- endpoints;
- methods;
- request schemas;
- response schemas;
- error format;
- warning format;
- pagination;
- filters.

---

### `docs/testing.md`

Стратегия тестирования:

- backend unit tests;
- frontend build/smoke;
- migration tests;
- packaging tests;
- manual MVP smoke;
- acceptance scenarios.

---

### `docs/decisions/`

ADR — Architecture Decision Records.

Фиксируют не только “что решили”, но и “почему”.

Минимальный набор:

```text
0001-local-first.md
0002-sqlite-mvp.md
0003-recipe-versioning.md
0004-user-data-directory.md
0005-import-drafts.md
0006-local-launcher.md
0007-onboarding-required.md
0008-client-wishes-feedback.md
```

---

## 4. Папка `state/`

`state/` хранит текущую память разработки.

В отличие от `docs/`, эти файлы регулярно меняются.

---

### `state/progress.md`

Текущий прогресс проекта.

Шаблон:

```markdown
# Progress

## Current phase

PR1 — App shell

## Done

- PR0 — Docs contract

## In progress

- Backend health endpoint
- Frontend shell
- Basic navigation

## Blocked

- none

## Next

- PR2 — DB + settings + audit

## Important notes

- Do not start inventory before PR5.
- Keep user data outside repo from D1.
```

---

### `state/handoff.md`

Передача контекста между сессиями.

Шаблон:

```markdown
# Handoff

## Last completed work

...

## Current repo state

...

## Important decisions

...

## Known issues

...

## Next recommended task

...

## Commands run

...

## Tests status

...
```

---

### `state/current-focus.md`

Текущий фокус Codex.

Шаблон:

```markdown
# Current Focus

Current task: PR1 — App shell

Allowed scope:
- backend health endpoint
- frontend shell
- base navigation

Do not touch:
- inventory
- recipes
- orders
- production
- packaging
- OCR
- cloud

Acceptance:
- backend starts
- frontend starts
- health status displayed
```

---

### `state/change-requests.md`

Журнал пожеланий и изменений.

Шаблон:

```markdown
# Change Requests

| ID | Date | Request | Status | Target PR | Notes |
|---|---|---|---|---|---|
| CR-001 | 2026-06-20 | Add onboarding checklist | accepted | O3 | Required for non-technical user |
```

---

## 5. Nested `AGENTS.md`

Nested `AGENTS.md` нужны для локальных правил.

---

### `backend/AGENTS.md`

Содержит:

- бизнес-логику держать в domain services;
- изменения БД только через миграции;
- Decimal для расчетов;
- производство transactional;
- импорт только через drafts;
- audit важных действий;
- не писать чувствительные заметки в логи;
- тесты обязательны.

---

### `frontend/AGENTS.md`

Содержит:

- UI должен быть человекопонятным;
- не показывать raw technical errors;
- каждый empty state должен иметь next action;
- dangerous actions require confirmation;
- статусы на русском;
- использовать shared UI components;
- не держать критичные расчеты только во frontend.

---

### `launcher/AGENTS.md`

Содержит:

- user data outside app;
- user mode не требует terminal;
- backend localhost only;
- auto-backup before migrations;
- graceful startup/shutdown;
- package must not include user database.

---

### `docs/AGENTS.md`

Содержит:

- docs должны быть краткими;
- обновлять docs при изменении архитектуры;
- не хранить секреты;
- различать product docs, current state и user help;
- пользовательские инструкции писать простым языком.

---

## 6. Папка `help/`

`help/` содержит офлайн-справку внутри приложения.

Это не dev-документация.  
Это инструкции для пользователя.

Минимальный набор:

```text
how-to-create-recipe.md
how-to-add-ingredient.md
how-to-add-client.md
how-to-create-order.md
how-to-produce-order.md
how-to-create-backup.md
what-is-density.md
what-is-lot.md
what-is-client-recipe.md
```

---

## 7. Как Codex должен использовать эти файлы

Перед каждой задачей:

```text
1. Read AGENTS.md
2. Read relevant nested AGENTS.md
3. Read docs/architecture.md
4. Read docs/roadmap.md
5. Read state/current-focus.md
6. Read state/progress.md
```

После значимой работы:

```text
1. Update state/progress.md
2. Update state/handoff.md
3. Update docs if architecture/API/roadmap changed
4. Add/update ADR if key architecture decision changed
```

---

## 8. Что не нужно делать

Не нужно:

- складывать все в один огромный `AGENTS.md`;
- делать `memory-bank/` единственным местом истины;
- дублировать один и тот же текст в 5 файлах;
- хранить секреты в документах;
- писать длинные философские инструкции для Codex;
- смешивать user docs и dev docs;
- хранить текущий прогресс в `README.md`;
- хранить бизнес-правила только в prompts;
- забывать обновлять `state/handoff.md`.

---

## 9. Рекомендуемый первый commit документации

Для старта достаточно создать:

```text
AGENTS.md
README.md
docs/architecture.md
docs/roadmap.md
docs/product-spec.md
docs/domain-model.md
docs/ui-ux-contract.md
state/progress.md
state/handoff.md
state/current-focus.md
code_review.md
```

Остальные файлы можно добавлять по мере реализации этапов.

---

## 10. Минимальный `AGENTS.md` для старта

```markdown
# AGENTS.md

You are working on `cosmetic-workshop-os`.

This is a local-first web app for a cosmetic workshop. The user is non-technical. The app must manage recipes, client formulas, clients, wishes/feedback, ingredients, lots, packaging, orders, production, alerts, purchases, imports, exports, backups and onboarding.

Before every task read:

- `docs/architecture.md`
- `docs/roadmap.md`
- `state/current-focus.md`
- `state/progress.md`
- relevant nested `AGENTS.md`

Hard rules:

- MVP is local-first.
- User data must stay outside app/repo.
- SQLite schema changes require migrations.
- Use Decimal for recipe, weight, density and money calculations.
- RecipeTemplate, RecipeVersion and ClientRecipe are separate concepts.
- Inventory changes must go through StockMovement.
- Production must be transactional.
- Imports must go through ImportDraft and user confirmation.
- UI must be human-readable and non-technical.
- One PR = one roadmap step.
- Do not add cloud, mobile, OCR, AI recommendations or advanced analytics unless explicitly scoped.
- No secrets in code or docs.

After meaningful work update:

- `state/progress.md`
- `state/handoff.md`
- relevant docs if contracts changed.

PR summary must include:

- Summary
- Scope
- Data model / migrations
- User-visible changes
- Tests
- Risks / limitations
- Follow-up
```

---

## 11. Итог

Правильная упаковка проектной логики в Markdown выглядит так:

```text
AGENTS.md = короткий контракт
docs/ = стабильная проектная документация
state/ = текущая память и прогресс
help/ = справка для пользователя
nested AGENTS.md = локальные правила для зон кода
ADR = история важных решений
code_review.md = контроль качества PR
```

Такой формат позволяет Codex работать как новый разработчик, который каждый раз получает:

- инструкцию;
- архитектуру;
- текущий фокус;
- историю прогресса;
- правила качества;
- ограничения продукта.

Главная цель:

```text
не просто дать Codex много текста,
а дать ему правильную карту проекта,
чтобы он делал маленькие безопасные PR
и не ломал архитектурные решения.
```
